"""
Whisper Validator - Transcription et scoring GPT des candidats
"""

import os
import subprocess
import openai
from datetime import datetime
from typing import List, Dict


def log(message: str, level: str = "INFO"):
    """Logging avec timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    prefix = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "•")
    print(f"[{timestamp}] {prefix} {message}")


def extract_audio_segment(video_path: str, start: float, end: float, output_path: str) -> bool:
    """
    Extrait un segment audio de la vidéo

    Args:
        video_path: Chemin vidéo source
        start: Début en secondes
        end: Fin en secondes
        output_path: Chemin de sortie MP3

    Returns:
        True si succès
    """
    duration = end - start

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start),
        '-i', video_path,
        '-t', str(duration),
        '-vn',  # Pas de vidéo
        '-acodec', 'libmp3lame',
        '-ar', '16000',  # 16kHz pour Whisper
        '-ac', '1',  # Mono
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"Erreur extraction audio : {result.stderr}", "ERROR")
        return False

    return True


def transcribe_with_whisper(audio_path: str, api_key: str) -> str:
    """
    Transcription avec OpenAI Whisper API

    Args:
        audio_path: Chemin vers fichier audio
        api_key: Clé API OpenAI

    Returns:
        Transcription texte
    """
    log(f"Transcription Whisper : {audio_path}", "DEBUG")

    openai.api_key = api_key

    try:
        with open(audio_path, 'rb') as audio_file:
            response = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language="fr"  # Forcer français
            )

        transcription = response['text'].strip()
        log(f"✅ Transcription : {transcription[:100]}...", "SUCCESS")
        return transcription

    except Exception as e:
        log(f"Erreur Whisper : {e}", "ERROR")
        return ""


def score_transcription_with_gpt(transcription: str, api_key: str) -> Dict:
    """
    Score une transcription avec GPT

    Critères :
    - Phrase complète (pas coupée)
    - Contenu engageant (question, révélation, punchline, action)
    - Pas juste musique/bruit
    - Contexte clair

    Args:
        transcription: Texte à scorer
        api_key: Clé API OpenAI

    Returns:
        {
            'score': float,  # 0-1
            'reason': str,
            'is_engaging': bool
        }
    """
    log(f"Scoring GPT de : '{transcription[:80]}'...", "DEBUG")

    openai.api_key = api_key

    prompt = f"""Tu es un expert en contenu viral pour YouTube Shorts.

Évalue cette transcription d'un extrait vidéo et donne un score de 0 à 1.

Critères pour un BON score (proche de 1) :
- Phrase complète et contexte clair
- Contenu engageant : question intrigante, révélation, punchline, moment d'action
- Langage naturel et fluide
- Potentiel viral (émotion, surprise, curiosité)

Critères pour un MAUVAIS score (proche de 0) :
- Phrase coupée ou incomplète
- Pas de contexte clair
- Juste de la musique, des bruits, ou du remplissage
- Ennuyeux, banal

Transcription à évaluer :
"{transcription}"

Réponds UNIQUEMENT avec ce format JSON :
{{
    "score": 0.X,
    "reason": "Courte explication",
    "is_engaging": true/false
}}"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en analyse de contenu viral."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        content = response.choices[0].message.content.strip()
        log(f"Réponse GPT : {content}", "DEBUG")

        # Parser le JSON
        import json
        try:
            # Extraire le JSON si entouré de ```
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content.strip())
        except:
            # Fallback si parsing échoue
            log("Impossible de parser la réponse GPT, score par défaut", "WARNING")
            result = {
                'score': 0.5,
                'reason': 'Parsing failed',
                'is_engaging': False
            }

        log(f"✅ Score GPT : {result['score']:.2f} - {result['reason']}", "SUCCESS")
        return result

    except Exception as e:
        log(f"Erreur GPT : {e}", "ERROR")
        return {
            'score': 0.0,
            'reason': f'Error: {str(e)}',
            'is_engaging': False
        }


def validate_candidates_with_whisper(
    video_path: str,
    candidates: List[Dict],
    top_n: int,
    openai_api_key: str,
    context_seconds: int = 5
) -> List[Dict]:
    """
    Valide les TOP N candidats avec Whisper + GPT

    Args:
        video_path: Chemin vidéo
        candidates: Liste des candidats avec scores audio-visuels
        top_n: Nombre de candidats à valider (ex: 5)
        openai_api_key: Clé API OpenAI
        context_seconds: Secondes avant/après le pic à transcrire (défaut: 5)

    Returns:
        Liste des candidats enrichis avec :
        - whisper_transcription
        - whisper_gpt_score
        - whisper_gpt_reason
        - final_score (combiné audio-visuel + whisper-gpt)
    """
    log("\n" + "=" * 80)
    log("🎙️ VALIDATION WHISPER + GPT", "INFO")
    log("=" * 80)
    log(f"Nombre de candidats à valider : {top_n}", "INFO")
    log(f"Contexte : ±{context_seconds}s autour du pic", "INFO")
    log("")

    # Prendre les TOP N
    top_candidates = candidates[:top_n]

    for i, candidate in enumerate(top_candidates):
        log("=" * 80)
        log(f"CANDIDAT #{i+1}/{len(top_candidates)}", "INFO")
        log("=" * 80)
        log(f"Segment : {candidate['start']:.1f}s - {candidate['end']:.1f}s", "INFO")
        log(f"Score audio-visuel : {candidate['combined_score']:.2f}", "INFO")
        log(f"Raison : {candidate['reason']}", "DEBUG")
        log("")

        # Extraire le centre du segment (pic présumé)
        center = (candidate['start'] + candidate['end']) / 2

        # Segment à transcrire : ±context_seconds autour du centre
        whisper_start = max(0, center - context_seconds)
        whisper_end = center + context_seconds

        log(f"Centre du segment : {center:.1f}s", "DEBUG")
        log(f"Extraction audio : {whisper_start:.1f}s - {whisper_end:.1f}s (durée: {whisper_end - whisper_start:.1f}s)", "INFO")

        # Extraire audio
        temp_audio = f"/tmp/candidate_{i}_audio.mp3"
        if not extract_audio_segment(video_path, whisper_start, whisper_end, temp_audio):
            log("Échec extraction audio, skip", "ERROR")
            candidate['whisper_transcription'] = ""
            candidate['whisper_gpt_score'] = 0.0
            candidate['whisper_gpt_reason'] = "Échec extraction audio"
            candidate['final_score'] = candidate['combined_score']
            continue

        log(f"✅ Audio extrait : {temp_audio}", "SUCCESS")

        # Transcription Whisper
        log("Lancement transcription Whisper...", "INFO")
        transcription = transcribe_with_whisper(temp_audio, openai_api_key)

        if not transcription:
            log("Transcription vide, score 0", "WARNING")
            candidate['whisper_transcription'] = ""
            candidate['whisper_gpt_score'] = 0.0
            candidate['whisper_gpt_reason'] = "Transcription vide"
            candidate['final_score'] = candidate['combined_score'] * 0.7  # Pénalité
        else:
            candidate['whisper_transcription'] = transcription
            log(f"📝 Transcription : '{transcription}'", "INFO")
            log("")

            # Scoring GPT
            log("Lancement scoring GPT...", "INFO")
            gpt_result = score_transcription_with_gpt(transcription, openai_api_key)

            candidate['whisper_gpt_score'] = gpt_result['score']
            candidate['whisper_gpt_reason'] = gpt_result['reason']
            candidate['is_engaging'] = gpt_result['is_engaging']

            # Score final : 50% audio-visuel + 50% whisper-gpt
            candidate['final_score'] = (
                0.5 * candidate['combined_score'] +
                0.5 * candidate['whisper_gpt_score']
            )

            log(f"📊 Score Whisper-GPT : {candidate['whisper_gpt_score']:.2f}", "INFO")
            log(f"📊 Score FINAL : {candidate['final_score']:.2f}", "SUCCESS")
            log(f"💬 Raison : {candidate['whisper_gpt_reason']}", "INFO")

        # Nettoyer
        try:
            os.remove(temp_audio)
        except:
            pass

        log("")

    # Trier par score final
    top_candidates.sort(key=lambda x: x['final_score'], reverse=True)

    log("=" * 80)
    log("🏆 CLASSEMENT FINAL", "SUCCESS")
    log("=" * 80)
    for i, c in enumerate(top_candidates):
        log(f"#{i+1} : {c['start']:.1f}s - {c['end']:.1f}s | Score final: {c['final_score']:.2f}", "INFO")
        log(f"       Audio-visuel: {c['combined_score']:.2f} | Whisper-GPT: {c.get('whisper_gpt_score', 0):.2f}", "DEBUG")
        log(f"       Transcription: '{c.get('whisper_transcription', 'N/A')[:80]}'", "DEBUG")
        log(f"       Raison GPT: {c.get('whisper_gpt_reason', 'N/A')}", "DEBUG")
        log("")

    return top_candidates
