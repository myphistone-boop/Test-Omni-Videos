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

    # Log pour debug
    print(f"[DEBUG] URL: {url}")
    print(f"[DEBUG] Cookies: {cookies_file} (exists: {Path(cookies_file).exists()})")

    # Options yt-dlp - Laisser choisir automatiquement le meilleur client
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bv*+ba/b',  # Évite les formats HLS qui donnent 403
        'merge_output_format': 'mp4',  # Convertit en MP4 après téléchargement
        'quiet': False,  # Verbose pour debug
        'no_warnings': False,
        'nocheckcertificate': True,
        'cookiefile': cookies_file if Path(cookies_file).exists() else None,
        'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},  # Skip HLS/DASH qui donnent 403
        # Ne pas spécifier de client - laisser yt-dlp choisir automatiquement
        # avec les cookies fournis
    }

    print(f"[DEBUG] Starting download...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # D'abord extraire les infos pour voir ce qui est disponible
        try:
            info = ydl.extract_info(url, download=False)
            print(f"[DEBUG] Video title: {info.get('title', 'Unknown')}")
            print(f"[DEBUG] Available formats count: {len(info.get('formats', []))}")

            # Afficher les 5 meilleurs formats
            if 'formats' in info and info['formats']:
                print(f"[DEBUG] Top formats available:")
                for i, fmt in enumerate(info['formats'][:5]):
                    print(f"  - {fmt.get('format_id')}: {fmt.get('ext')} {fmt.get('resolution', 'audio')} {fmt.get('filesize', 0) / 1024 / 1024:.1f}MB")
        except Exception as e:
            print(f"[DEBUG] Error extracting info: {e}")
            raise

        # Maintenant télécharger
        print(f"[DEBUG] Downloading...")
        ydl.download([url])

    print(f"[DEBUG] Download complete: {output_path}")
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
