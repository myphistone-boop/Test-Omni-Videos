"""
Video processor pour le backend SaaS
Transforme des vidéos en shorts avec sous-titres
"""

import sys
import shutil
from pathlib import Path

# Ajouter le parent au path pour importer create_subtitled_video
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from create_subtitled_video import YouTubeSubtitleGenerator


def create_short_video(input_video: str, output_path: str, language: str = "fr"):
    """
    Crée un short à partir d'une vidéo existante

    Args:
        input_video: Chemin vers la vidéo source
        output_path: Chemin où sauvegarder le short
        language: Langue des sous-titres (fr ou en)

    Returns:
        str: Chemin du fichier créé
    """

    # Créer le générateur
    generator = YouTubeSubtitleGenerator()

    video_title = Path(input_video).stem

    print("\n" + "=" * 70)
    print("🎥 GÉNÉRATEUR DE SOUS-TITRES - MODE AUTOMATIQUE")
    print("=" * 70)

    # Étape 1: Extraire l'audio
    print("\n🎵 Extraction de l'audio...")
    audio_path = generator.extraire_audio(input_video, video_title)

    # Étape 2: Transcrire avec Whisper
    print("\n🎙️ Transcription avec Whisper...")
    transcript = generator.transcrire_avec_whisper(audio_path, video_title)

    # Étape 3: Créer le short TikTok optimisé
    print("\n🎬 Création du short TikTok optimisé...")
    generated_video = generator.creer_video_tiktok_optimisee(
        video_path=input_video,
        transcript=transcript,
        video_title=video_title
    )

    # Copier le fichier généré vers le chemin de sortie souhaité
    if generated_video and Path(generated_video).exists():
        shutil.copy2(generated_video, output_path)
        print(f"✅ Vidéo copiée vers: {output_path}")
        return output_path
    else:
        raise Exception(f"Échec de la génération de la vidéo. Fichier non trouvé: {generated_video}")
