"""
YouTube downloader pour le backend SaaS
Télécharge des vidéos YouTube via yt-dlp
"""

import yt_dlp
import os


def download_video(url: str, output_path: str):
    """
    Télécharge une vidéo YouTube

    Args:
        url: URL de la vidéo YouTube
        output_path: Chemin complet où sauvegarder la vidéo

    Returns:
        str: Chemin du fichier téléchargé
    """

    # Options yt-dlp
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path
