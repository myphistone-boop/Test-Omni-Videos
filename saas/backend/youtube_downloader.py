"""
YouTube downloader pour le backend SaaS
Télécharge des vidéos YouTube via yt-dlp
"""

import yt_dlp
import os
from pathlib import Path


def download_video(url: str, output_path: str):
    """
    Télécharge une vidéo YouTube

    Args:
        url: URL de la vidéo YouTube
        output_path: Chemin complet où sauvegarder la vidéo

    Returns:
        str: Chemin du fichier téléchargé
    """

    # Chemin des cookies (optionnel)
    cookies_file = "/home/shorts/cookies.txt"

    # Options yt-dlp
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Ajouter les cookies si le fichier existe
        'cookiefile': cookies_file if Path(cookies_file).exists() else None,
        # Options anti-détection
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        # Headers pour simuler un navigateur
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path
