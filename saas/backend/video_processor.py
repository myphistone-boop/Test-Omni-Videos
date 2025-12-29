"""
Video processor pour le backend SaaS
Transforme des vidéos en shorts avec sous-titres
"""

import sys
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

    # Traiter la vidéo (elle utilise déjà le fichier local)
    # La méthode traiter_video accepte un fichier local
    generator.traiter_video(
        video_path=input_video,
        output_path=output_path,
        language=language
    )

    return output_path
