"""
YouTube downloader pour le backend SaaS
Télécharge des vidéos YouTube via yt-dlp avec cookies utilisateur
"""

import yt_dlp
import os
from pathlib import Path


def download_with_ytdlp(url: str, output_path: str, cookies_path: str = None) -> str:
    """
    Télécharge via yt-dlp (avec ou sans cookies)

    Args:
        url: URL YouTube
        output_path: Chemin de sortie
        cookies_path: Chemin cookies (optionnel)

    Returns:
        str: Chemin du fichier
    """

    # Utiliser le cookies_path fourni, sinon fallback sur le global
    if cookies_path is None:
        cookies_path = "/home/shorts/cookies.txt"

    cookies_file = cookies_path

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


def download_video(url: str, output_path: str, cookies_path: str = None):
    """
    Télécharge une vidéo YouTube

    Stratégie simple:
    - Si cookies fournis → téléchargement avec yt-dlp
    - Sinon → erreur explicite demandant les cookies

    Args:
        url: URL de la vidéo YouTube
        output_path: Chemin complet où sauvegarder la vidéo
        cookies_path: Chemin vers le fichier cookies.txt (REQUIS)

    Returns:
        str: Chemin du fichier téléchargé

    Raises:
        Exception: Si pas de cookies ou échec du téléchargement
    """

    # Vérifier si les cookies sont fournis
    if not cookies_path or not Path(cookies_path).exists():
        raise Exception(
            "Cookies YouTube requis pour télécharger les vidéos. "
            "Veuillez uploader votre fichier cookies.txt. "
            "Instructions: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
        )

    # Télécharger avec cookies
    return download_with_ytdlp(url, output_path, cookies_path)
