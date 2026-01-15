"""
Video processor RAPIDE pour le backend SaaS
Pipeline optimisé : 2 passes au lieu de 6
"""

import sys
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

# Ajouter le parent au path pour importer create_subtitled_video
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from create_subtitled_video import YouTubeSubtitleGenerator


def create_short_video_fast(input_video: str, output_path: str, language: str = "fr",
                           progress_callback=None, youtube_url: str = None,
                           transcription_mode: str = "youtube_subs", cookies_path: str = None,
                           openai_api_key: str = None):
    """
    Crée un short RAPIDEMENT avec pipeline optimisé

    Pipeline ULTRA-RAPIDE (3 modes):
    MODE 1 - YouTube Subs (gratuit, rapide):
    1. Sous-titres YouTube → Transcription
    2. EXTRACTION des 60-90s les plus virales
    3. Génération fichier .ass sous-titres (sur 60s seulement)
    4. UNE SEULE PASSE FFmpeg sur 60s : vertical 720p + fond noir + sous-titres

    MODE 2 - Audio-Visual + Whisper (nouveau, intelligent):
    1. Analyse audio+visuel → 15 candidats temps forts
    2. TOP 5 → Whisper + GPT scoring
    3. Meilleur segment → Whisper pour sous-titres
    4. UNE SEULE PASSE FFmpeg

    MODE 3 - Whisper complet (fallback):
    1. Transcription Whisper complète
    2. Détection moments forts
    3. Génération short

    Args:
        input_video: Chemin vers la vidéo source
        output_path: Chemin où sauvegarder le short
        language: Langue des sous-titres (fr ou en)
        progress_callback: Fonction optionnelle callback(progress, message)
        youtube_url: URL YouTube (requis si transcription_mode='youtube_subs')
        transcription_mode: Mode de transcription ('youtube_subs', 'audio_visual', ou 'whisper')
        cookies_path: Chemin vers cookies.txt (requis pour YouTube subtitles)
        openai_api_key: Clé API OpenAI (requis pour modes 'audio_visual' et 'whisper')

    Returns:
        str: Chemin du fichier créé
    """

    # N'instancier YouTubeSubtitleGenerator QUE si on utilise Whisper
    # (car cette classe vérifie la clé OpenAI à l'initialisation)
    generator = None
    if transcription_mode == "whisper":
        generator = YouTubeSubtitleGenerator()

    video_title = Path(input_video).stem

    print("\n" + "=" * 70)
    print(f"⚡ GÉNÉRATEUR ULTRA-RAPIDE - MODE: {transcription_mode.upper()}")
    print("=" * 70)

    # Étape 1 & 2: Obtenir la transcription OU utiliser analyse audio-visuelle
    transcript_words = None
    best_segment = None  # Pour le mode audio_visual

    if transcription_mode == "youtube_subs" and youtube_url:
        # MODE 1: Sous-titres YouTube (GRATUIT, ULTRA-RAPIDE)
        print("\n🎬 Récupération des sous-titres YouTube...")
        if progress_callback:
            progress_callback(35, "Récupération des sous-titres YouTube...")

        from youtube_downloader import download_youtube_subtitles
        transcript_words = download_youtube_subtitles(youtube_url, language, cookies_path=cookies_path)

        if transcript_words:
            print(f"✅ {len(transcript_words)} mots récupérés des sous-titres YouTube (gratuit!)")
        else:
            print("⚠️  Pas de sous-titres YouTube, basculement vers mode audio-visuel...")
            transcription_mode = "audio_visual"  # Fallback automatique

    if transcription_mode == "audio_visual":
        # MODE 2: Audio-Visual + Whisper sur TOP 5 (INTELLIGENT, RAPIDE, PEU CHER)
        print("\n" + "=" * 80)
        print("🎯 MODE AUDIO-VISUEL ACTIVÉ")
        print("=" * 80)
        print("")

        if not openai_api_key:
            raise Exception("Clé API OpenAI requise pour le mode audio-visuel")

        if progress_callback:
            progress_callback(20, "Analyse audio-visuelle...")

        # Obtenir la durée de la vidéo
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(input_video)
        duree_totale = video.duration
        video.close()

        # 1. Analyse audio-visuelle
        from audio_visual_analyzer import analyze_video
        candidates = analyze_video(input_video, duree_totale)

        if not candidates:
            print("❌ Aucun candidat détecté par l'analyse audio-visuelle")
            print("⚠️  Basculement vers Whisper complet...")
            transcription_mode = "whisper"
        else:
            if progress_callback:
                progress_callback(40, "Validation Whisper des TOP 5 candidats...")

            # 2. Whisper + GPT sur TOP 5
            from whisper_validator import validate_candidates_with_whisper
            validated_candidates = validate_candidates_with_whisper(
                video_path=input_video,
                candidates=candidates,
                top_n=5,
                openai_api_key=openai_api_key,
                context_seconds=5
            )

            if not validated_candidates or validated_candidates[0]['final_score'] < 0.3:
                print("⚠️  Aucun candidat avec score suffisant, basculement vers Whisper complet...")
                transcription_mode = "whisper"
            else:
                # 3. Prendre le meilleur
                best_segment = validated_candidates[0]
                print("\n" + "=" * 80)
                print(f"🏆 MEILLEUR SEGMENT SÉLECTIONNÉ")
                print("=" * 80)
                print(f"Segment : {best_segment['start']:.1f}s - {best_segment['end']:.1f}s")
                print(f"Score final : {best_segment['final_score']:.2f}")
                print(f"Transcription : '{best_segment.get('whisper_transcription', 'N/A')[:100]}'")
                print("")

                # 4. Whisper sur ce segment pour les sous-titres
                if progress_callback:
                    progress_callback(60, "Génération sous-titres du meilleur segment...")

                # On a déjà la transcription, mais on a besoin du format avec timestamps mot-par-mot
                # Donc on va re-transcribe avec Whisper le segment choisi
                if generator is None:
                    generator = YouTubeSubtitleGenerator()

                # Extraire le segment audio
                segment_start = best_segment['start']
                segment_end = min(segment_start + 60, best_segment['end'])  # Max 60s

                print(f"📝 Transcription Whisper du segment {segment_start:.1f}s - {segment_end:.1f}s...")

                # Extraire audio du segment
                segment_audio_path = str(Path(tempfile.gettempdir()) / f"{video_title}_segment_audio.mp3")

                extract_audio_cmd = [
                    'ffmpeg', '-y',
                    '-ss', str(segment_start),
                    '-i', input_video,
                    '-t', str(segment_end - segment_start),
                    '-vn',
                    '-acodec', 'libmp3lame',
                    '-ar', '16000',
                    '-ac', '1',
                    segment_audio_path
                ]

                result = subprocess.run(extract_audio_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Erreur extraction audio : {result.stderr}")
                    raise Exception("Échec extraction audio segment")

                # Transcrire avec Whisper
                transcript = generator.transcrire_avec_whisper(segment_audio_path, video_title)

                # Convertir au format unifié
                # IMPORTANT: Ajuster les timestamps pour qu'ils soient relatifs à la vidéo complète
                transcript_words = []
                for mot in transcript.words:
                    transcript_words.append({
                        'word': mot.word,
                        'start': mot.start + segment_start,  # Ajuster au temps absolu
                        'end': mot.end + segment_start       # Ajuster au temps absolu
                    })

                # Nettoyer
                try:
                    Path(segment_audio_path).unlink()
                except:
                    pass

                print(f"✅ {len(transcript_words)} mots transcrits (timestamps ajustés: {segment_start:.1f}s - {segment_end:.1f}s)")

                # DEBUG: Afficher quelques mots pour vérifier les timestamps
                if transcript_words:
                    print(f"   🔍 DEBUG - Premier mot: '{transcript_words[0]['word']}' @ {transcript_words[0]['start']:.1f}s")
                    print(f"   🔍 DEBUG - Dernier mot: '{transcript_words[-1]['word']}' @ {transcript_words[-1]['start']:.1f}s")

    if transcription_mode == "whisper" or (transcript_words is None and transcription_mode == "whisper"):
        # MODE 3: Whisper API complet (PAYANT mais FIABLE - FALLBACK)
        if generator is None:
            generator = YouTubeSubtitleGenerator()

        print("\n🎵 Extraction de l'audio...")
        if progress_callback:
            progress_callback(35, "Extraction audio...")

        audio_path = generator.extraire_audio(input_video, video_title)

        print("\n🎙️ Transcription avec Whisper API...")
        if progress_callback:
            progress_callback(40, "Transcription Whisper (peut prendre 1-4 min selon la durée)...")

        transcript = generator.transcrire_avec_whisper(audio_path, video_title)

        # Convertir au format unifié
        transcript_words = []
        for mot in transcript.words:
            transcript_words.append({
                'word': mot.word,
                'start': mot.start,
                'end': mot.end
            })

    if not transcript_words:
        raise Exception("Impossible d'obtenir la transcription")

    # Créer un objet mock transcript avec attribut 'words' pour la détection virale
    class MockWord:
        def __init__(self, word, start, end):
            self.word = word
            self.start = start
            self.end = end

    class MockTranscript:
        def __init__(self, words_list):
            self.words = [MockWord(w['word'], w['start'], w['end']) for w in words_list]

    mock_transcript = MockTranscript(transcript_words)

    # Étape 3: Déterminer le segment à utiliser
    from moviepy.editor import VideoFileClip
    video = VideoFileClip(input_video)
    duree_totale = video.duration
    video.close()

    duree_souhaitee = min(60, duree_totale)  # Max 60 secondes

    if best_segment:
        # MODE AUDIO-VISUEL: Utiliser le segment sélectionné
        debut_segment = best_segment['start']
        fin_segment = min(debut_segment + duree_souhaitee, best_segment['end'])

        print("\n" + "=" * 80)
        print("✨ UTILISATION DU SEGMENT AUDIO-VISUEL")
        print("=" * 80)
        print(f"Segment : {int(debut_segment)}s → {int(fin_segment)}s (durée: {int(fin_segment - debut_segment)}s)")
        print(f"Score : {best_segment['final_score']:.2f}")
        print(f"Raison : {best_segment.get('whisper_gpt_reason', best_segment.get('reason', 'N/A'))}")
        print(f"🔍 DEBUG - best_segment original: start={best_segment['start']:.1f}s, end={best_segment['end']:.1f}s")
        print(f"🔍 DEBUG - duree_souhaitee={duree_souhaitee}s, duree_totale={duree_totale:.1f}s")
        print("")
    else:
        # MODE CLASSIQUE: Détection moments forts depuis transcription
        print("\n🔥 Détection du segment viral optimal (60-90s)...")
        if progress_callback:
            progress_callback(50, "Analyse des moments viraux...")

        moments_forts = generator.detecter_moments_forts_local(mock_transcript, duree_segment=3)

        if moments_forts and duree_totale > duree_souhaitee:
            # Prendre le moment fort avec le meilleur score
            meilleur_moment = moments_forts[0]
            debut_segment = max(0, meilleur_moment['start'] - 5)  # 5s avant le moment fort
            fin_segment = min(debut_segment + duree_souhaitee, duree_totale)
            print(f"   ✨ Segment viral trouvé : {int(debut_segment)}s → {int(fin_segment)}s")
            print(f"   💡 Raison : {meilleur_moment.get('reason', 'N/A')}")
        else:
            # Prendre le début si pas de moment fort ou vidéo courte
            debut_segment = 0
            fin_segment = min(duree_souhaitee, duree_totale)
            print(f"   📍 Utilisation du début : 0s → {int(fin_segment)}s")

    # Étape 4: Extraire le segment viral AVANT traitement
    print(f"\n✂️  Extraction du segment ({int(fin_segment - debut_segment)}s)...")
    if progress_callback:
        progress_callback(55, "Extraction du segment viral...")

    segment_path = str(Path(tempfile.gettempdir()) / f"{video_title}_segment.mp4")

    # Utiliser FFmpeg pour extraire le segment avec réencodage
    # -ss AVANT -i = seek plus rapide, réencoder évite le freeze au début
    extract_cmd = [
        'ffmpeg',
        '-ss', str(debut_segment),  # -ss AVANT -i = plus rapide
        '-i', input_video,
        '-t', str(fin_segment - debut_segment),
        '-c:v', 'libx264',  # Réencoder pour éviter freeze
        '-preset', 'ultrafast',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-y',
        segment_path
    ]

    print(f"   ▶️  Extraction du segment avec FFmpeg (peut prendre 5-15s)...")
    import sys
    sys.stdout.flush()

    result = subprocess.run(extract_cmd)

    print(f"   ✅ Segment extrait (code retour: {result.returncode})")
    sys.stdout.flush()

    if result.returncode != 0:
        print(f"❌ Erreur extraction : code retour {result.returncode}")
        raise Exception(f"Échec extraction segment: code retour {result.returncode}")

    if progress_callback:
        progress_callback(65, "Segment extrait, préparation des sous-titres...")

    # Étape 5: Filtrer la transcription pour ce segment uniquement
    print("\n📝 Génération des sous-titres (segment uniquement)...")
    print(f"🔍 DEBUG - Filtrage des mots entre {debut_segment:.1f}s et {fin_segment:.1f}s")
    print(f"🔍 DEBUG - Nombre total de mots transcrits: {len(transcript_words)}")

    # Filtrer les mots pour le segment viral sélectionné
    mots_filtres = []
    for mot_dict in transcript_words:
        if debut_segment <= mot_dict['start'] <= fin_segment:
            # Ajuster les timestamps relatifs au segment
            mots_filtres.append({
                'word': mot_dict['word'],
                'start': mot_dict['start'] - debut_segment,
                'end': mot_dict['end'] - debut_segment
            })

    print(f"🔍 DEBUG - Nombre de mots après filtrage: {len(mots_filtres)}")
    if len(mots_filtres) == 0:
        print(f"⚠️  WARNING - Aucun mot filtré! Les timestamps des mots ne correspondent pas à la plage du segment!")
        if transcript_words:
            print(f"   Premier mot transcrit @ {transcript_words[0]['start']:.1f}s")
            print(f"   Dernier mot transcrit @ {transcript_words[-1]['start']:.1f}s")
            print(f"   Plage attendue: {debut_segment:.1f}s - {fin_segment:.1f}s")

    # Créer le fichier .ass avec les mots filtrés
    ass_path = Path(tempfile.gettempdir()) / f"{video_title}_subtitles.ass"
    generator.creer_fichier_ass_anime(mots_filtres, str(ass_path))

    # Étape 6: UNE SEULE PASSE FFmpeg sur le segment court !
    print(f"\n⚡ Conversion 720p + Fond Noir + Sous-titres (sur {int(fin_segment - debut_segment)}s)...")
    print("   💡 Optimisations : 720p + fond noir = 2-3x plus rapide que 1080p + blur !")

    if progress_callback:
        progress_callback(70, "Création du short optimisé (traitement vidéo)...")

    # Commande FFmpeg ULTRA-OPTIMISÉE
    ffmpeg_cmd = [
        'ffmpeg', '-i', segment_path,
        '-filter_complex',
        # Fond noir 720x1280 (RAPIDE, pas de blur gourmand!)
        'color=black:s=720x1280[bg];'
        # Vidéo principale scalée en 720p
        '[0:v]scale=720:-2[fg];'
        # Overlay vidéo au centre + sous-titres
        '[bg][fg]overlay=(W-w)/2:(H-h)/2,subtitles=' + str(ass_path) + '[out]',
        '-map', '[out]',
        '-map', '0:a?',  # Copier l'audio si présent
        '-c:v', 'libx264',
        '-preset', 'ultrafast',  # ULTRA RAPIDE
        '-crf', '28',  # Qualité optimisée pour TikTok/Shorts
        '-c:a', 'aac',
        '-b:a', '128k',
        '-y',  # Overwrite
        output_path
    ]

    print(f"   🚀 Lancement FFmpeg...")

    # Flag pour savoir quand FFmpeg est terminé
    ffmpeg_done = threading.Event()

    def simulate_progress():
        """Simule la progression pendant l'encodage FFmpeg"""
        current_progress = 70
        while not ffmpeg_done.is_set() and current_progress < 88:
            time.sleep(2)  # Toutes les 2 secondes
            if not ffmpeg_done.is_set():
                current_progress += 1
                if progress_callback:
                    progress_callback(current_progress, f"Traitement vidéo en cours ({current_progress}%)...")

    # Lancer le thread de progression si callback fourni
    if progress_callback:
        progress_thread = threading.Thread(target=simulate_progress, daemon=True)
        progress_thread.start()

    print(f"   ▶️  Démarrage FFmpeg (cela peut prendre 10-30s pour un segment de 40s)...")
    print(f"   📊 Commande : {' '.join(ffmpeg_cmd[:5])}... ({len(ffmpeg_cmd)} arguments)")
    import sys
    sys.stdout.flush()

    # Lancer FFmpeg SANS capturer la sortie pour voir la progression en temps réel
    result = subprocess.run(ffmpeg_cmd)

    # Arrêter la simulation de progression
    ffmpeg_done.set()

    print(f"   ✅ FFmpeg terminé (code retour: {result.returncode})")
    sys.stdout.flush()

    if result.returncode != 0:
        print(f"❌ Erreur FFmpeg (code {result.returncode})")
        raise Exception(f"Échec FFmpeg: code retour {result.returncode}")

    if progress_callback:
        progress_callback(90, "Finalisation du short...")

    # Nettoyer les fichiers temporaires
    if ass_path.exists():
        ass_path.unlink()
    if Path(segment_path).exists():
        Path(segment_path).unlink()

    print(f"✅ Short créé avec succès : {output_path}")
    print(f"   ⏱️  Gain de temps : 5-10x plus rapide que traiter toute la vidéo !")
    print(f"   📏 Durée finale : {int(fin_segment - debut_segment)}s (optimisé pour TikTok/Shorts)")

    return output_path
