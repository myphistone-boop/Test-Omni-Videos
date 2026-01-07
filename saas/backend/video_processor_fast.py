"""
Video processor RAPIDE pour le backend SaaS
Pipeline optimisé : 2 passes au lieu de 6
"""

import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

# Ajouter le parent au path pour importer create_subtitled_video
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from create_subtitled_video import YouTubeSubtitleGenerator


def create_short_video_fast(input_video: str, output_path: str, language: str = "fr"):
    """
    Crée un short RAPIDEMENT avec pipeline optimisé

    Pipeline ULTRA-RAPIDE :
    1. Extraction audio + Transcription Whisper
    2. EXTRACTION des 60-90s les plus virales (au lieu de traiter 5 min!)
    3. Génération fichier .ass sous-titres (sur 60s seulement)
    4. UNE SEULE PASSE FFmpeg sur 60s : vertical 9:16 + flou + sous-titres

    Args:
        input_video: Chemin vers la vidéo source
        output_path: Chemin où sauvegarder le short
        language: Langue des sous-titres (fr ou en)

    Returns:
        str: Chemin du fichier créé
    """

    generator = YouTubeSubtitleGenerator()
    video_title = Path(input_video).stem

    print("\n" + "=" * 70)
    print("⚡ GÉNÉRATEUR ULTRA-RAPIDE - EXTRACTION 60s VIRALES")
    print("=" * 70)

    # Étape 1: Extraire l'audio
    print("\n🎵 Extraction de l'audio...")
    audio_path = generator.extraire_audio(input_video, video_title)

    # Étape 2: Transcrire avec Whisper
    print("\n🎙️ Transcription avec Whisper...")
    transcript = generator.transcrire_avec_whisper(audio_path, video_title)

    # Étape 3: NOUVEAUTÉ - Détecter et extraire segment viral (60-90s)
    print("\n🔥 Détection du segment viral optimal (60-90s)...")
    moments_forts = generator.detecter_moments_forts_local(transcript, duree_segment=3)

    # Déterminer le meilleur segment de 60-90s
    from moviepy.editor import VideoFileClip
    video = VideoFileClip(input_video)
    duree_totale = video.duration
    video.close()

    duree_souhaitee = min(60, duree_totale)  # Max 60 secondes

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

    result = subprocess.run(extract_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur extraction : {result.stderr}")
        raise Exception(f"Échec extraction segment: {result.stderr}")

    # Étape 5: Filtrer la transcription pour ce segment uniquement
    print("\n📝 Génération des sous-titres (segment uniquement)...")

    # Convertir transcript.words en format dict
    tous_mots = []
    for mot in transcript.words:
        tous_mots.append({
            'word': mot.word,
            'start': mot.start,
            'end': mot.end
        })

    # Filtrer pour le segment
    mots_filtres = []
    for mot_dict in tous_mots:
        if debut_segment <= mot_dict['start'] <= fin_segment:
            # Ajuster les timestamps relatifs au segment
            mots_filtres.append({
                'word': mot_dict['word'],
                'start': mot_dict['start'] - debut_segment,
                'end': mot_dict['end'] - debut_segment
            })

    # Créer le fichier .ass avec les mots filtrés
    ass_path = Path(tempfile.gettempdir()) / f"{video_title}_subtitles.ass"
    generator.creer_fichier_ass_anime(mots_filtres, str(ass_path))

    # Étape 6: UNE SEULE PASSE FFmpeg sur le segment court !
    print(f"\n⚡ Conversion 9:16 + Flou + Sous-titres (sur {int(fin_segment - debut_segment)}s)...")
    print("   💡 Traitement d'un segment court = 5-10x plus rapide !")

    # Commande FFmpeg optimisée sur le SEGMENT uniquement
    ffmpeg_cmd = [
        'ffmpeg', '-i', segment_path,
        '-filter_complex',
        # Split en 2 streams: background flouté + vidéo principale
        '[0:v]split=2[bg][fg];'
        # Background: scale + blur
        '[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg_blur];'
        # Foreground: scale pour garder aspect ratio dans 9:16
        '[fg]scale=1080:-2[fg_scaled];'
        # Overlay foreground sur background flouté (centré)
        '[bg_blur][fg_scaled]overlay=(W-w)/2:(H-h)/2,subtitles=' + str(ass_path) + '[out]',
        '-map', '[out]',
        '-map', '0:a?',  # Copier l'audio si présent
        '-c:v', 'libx264',
        '-preset', 'ultrafast',  # ULTRA RAPIDE
        '-crf', '23',  # Qualité correcte
        '-c:a', 'aac',
        '-b:a', '128k',
        '-y',  # Overwrite
        output_path
    ]

    print(f"   🚀 Lancement FFmpeg...")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Erreur FFmpeg: {result.stderr}")
        raise Exception(f"Échec FFmpeg: {result.stderr}")

    # Nettoyer les fichiers temporaires
    if ass_path.exists():
        ass_path.unlink()
    if Path(segment_path).exists():
        Path(segment_path).unlink()

    print(f"✅ Short créé avec succès : {output_path}")
    print(f"   ⏱️  Gain de temps : 5-10x plus rapide que traiter toute la vidéo !")
    print(f"   📏 Durée finale : {int(fin_segment - debut_segment)}s (optimisé pour TikTok/Shorts)")

    return output_path
