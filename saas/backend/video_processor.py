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

    # Traiter la vidéo (démarre à l'étape 2 car on a déjà la vidéo)
    # traiter_video retourne le chemin du fichier généré
    generated_video = generator.traiter_video(
        video_path=input_video,
        etape_depart=2  # Démarrer à l'extraction audio (vidéo déjà téléchargée)
    )

    # Copier le fichier généré vers le chemin de sortie souhaité
    if generated_video and Path(generated_video).exists():
        shutil.copy2(generated_video, output_path)
        print(f"✅ Vidéo copiée vers: {output_path}")
        return output_path
    else:
        raise Exception(f"Échec de la génération de la vidéo. Fichier non trouvé: {generated_video}")
