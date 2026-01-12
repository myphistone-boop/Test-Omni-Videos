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
                           transcription_mode: str = "youtube_subs"):
    """
    Crée un short RAPIDEMENT avec pipeline optimisé

    Pipeline ULTRA-RAPIDE :
    1. Transcription (YouTube subs OU Whisper)
    2. EXTRACTION des 60-90s les plus virales
    3. Génération fichier .ass sous-titres (sur 60s seulement)
    4. UNE SEULE PASSE FFmpeg sur 60s : vertical 720p + fond noir + sous-titres

    Args:
        input_video: Chemin vers la vidéo source
        output_path: Chemin où sauvegarder le short
        language: Langue des sous-titres (fr ou en)
        progress_callback: Fonction optionnelle callback(progress, message)
        youtube_url: URL YouTube (requis si transcription_mode='youtube_subs')
        transcription_mode: Mode de transcription ('youtube_subs' ou 'whisper')

    Returns:
        str: Chemin du fichier créé
    """

    generator = YouTubeSubtitleGenerator()
    video_title = Path(input_video).stem

    print("\n" + "=" * 70)
    print(f"⚡ GÉNÉRATEUR ULTRA-RAPIDE - MODE: {transcription_mode.upper()}")
    print("=" * 70)

    # Étape 1 & 2: Obtenir la transcription
    transcript_words = None

    if transcription_mode == "youtube_subs" and youtube_url:
        # MODE 1: Sous-titres YouTube (GRATUIT, ULTRA-RAPIDE)
        print("\n🎬 Récupération des sous-titres YouTube...")
        if progress_callback:
            progress_callback(35, "Récupération des sous-titres YouTube...")

        from youtube_downloader import download_youtube_subtitles
        transcript_words = download_youtube_subtitles(youtube_url, language)

        if transcript_words:
            print(f"✅ {len(transcript_words)} mots récupérés des sous-titres YouTube (gratuit!)")
        else:
            print("⚠️ Pas de sous-titres YouTube, fallback vers Whisper...")
            transcription_mode = "whisper"  # Fallback

    if transcription_mode == "whisper" or transcript_words is None:
        # MODE 2: Whisper API (PAYANT mais FIABLE)
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

    # Étape 3: NOUVEAUTÉ - Détecter et extraire segment viral (60-90s)
    print("\n🔥 Détection du segment viral optimal (60-90s)...")
    if progress_callback:
        progress_callback(50, "Analyse des moments viraux...")

    moments_forts = generator.detecter_moments_forts_local(mock_transcript, duree_segment=3)

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

    result = subprocess.run(extract_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erreur extraction : {result.stderr}")
        raise Exception(f"Échec extraction segment: {result.stderr}")

    if progress_callback:
        progress_callback(65, "Segment extrait, préparation des sous-titres...")

    # Étape 5: Filtrer la transcription pour ce segment uniquement
    print("\n📝 Génération des sous-titres (segment uniquement)...")

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

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    # Arrêter la simulation de progression
    ffmpeg_done.set()

    if result.returncode != 0:
        print(f"❌ Erreur FFmpeg: {result.stderr}")
        raise Exception(f"Échec FFmpeg: {result.stderr}")

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
