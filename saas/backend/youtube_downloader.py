"""
YouTube downloader pour le backend SaaS
Télécharge des vidéos YouTube via Cobalt API (fallback: yt-dlp)
"""

import yt_dlp
import os
import requests
from pathlib import Path


def download_with_cobalt(url: str, output_path: str) -> str:
    """
    Télécharge une vidéo YouTube via Cobalt API v9 (gratuit, pas de cookies requis)

    Args:
        url: URL de la vidéo YouTube
        output_path: Chemin où sauvegarder la vidéo

    Returns:
        str: Chemin du fichier téléchargé

    Raises:
        Exception: Si Cobalt API échoue
    """

    # Appel à Cobalt API v9 (nouvelle version depuis nov 2024)
    response = requests.post(
        "https://api.cobalt.tools/",
        json={
            "url": url,
            "videoQuality": "1080"
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(f"Cobalt API error: {response.status_code}")

    data = response.json()

    # Cobalt v9 retourne un format différent
    if data.get("status") == "error":
        raise Exception(f"Cobalt error: {data.get('text', 'Unknown error')}")

    # Extraire l'URL de la vidéo (format v9)
    video_url = data.get("url")
    if not video_url:
        raise Exception("Cobalt did not return video URL")

    # Télécharger la vidéo depuis l'URL fournie par Cobalt
    video_response = requests.get(video_url, stream=True, timeout=300)
    video_response.raise_for_status()

    # Sauvegarder la vidéo
    with open(output_path, 'wb') as f:
        for chunk in video_response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return output_path


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
    Télécharge une vidéo YouTube avec fallback intelligent

    Stratégie:
    1. Si cookies fournis → yt-dlp avec cookies (fiable)
    2. Sinon → Cobalt API (gratuit, pas de cookies)
    3. Si Cobalt échoue → yt-dlp sans cookies (dernière chance)

    Args:
        url: URL de la vidéo YouTube
        output_path: Chemin complet où sauvegarder la vidéo
        cookies_path: Chemin vers le fichier cookies.txt (optionnel)

    Returns:
        str: Chemin du fichier téléchargé

    Raises:
        Exception: Si toutes les méthodes échouent
    """

    errors = []

    # Stratégie 1: Si cookies fournis, utiliser yt-dlp avec cookies (prioritaire)
    if cookies_path and Path(cookies_path).exists():
        try:
            print(f"[Download] Tentative 1/2: yt-dlp avec cookies")
            return download_with_ytdlp(url, output_path, cookies_path)
        except Exception as e:
            errors.append(f"yt-dlp (cookies): {str(e)}")
            print(f"[Download] Échec yt-dlp avec cookies: {e}")

    # Stratégie 2: Cobalt API (gratuit, pas de cookies requis)
    try:
        print(f"[Download] Tentative {'2/2' if cookies_path else '1/2'}: Cobalt API (gratuit)")
        return download_with_cobalt(url, output_path)
    except Exception as e:
        errors.append(f"Cobalt API: {str(e)}")
        print(f"[Download] Échec Cobalt API: {e}")

    # Stratégie 3: yt-dlp sans cookies (dernière chance)
    try:
        print(f"[Download] Tentative finale: yt-dlp sans cookies")
        return download_with_ytdlp(url, output_path, cookies_path=None)
    except Exception as e:
        errors.append(f"yt-dlp (sans cookies): {str(e)}")
        print(f"[Download] Échec yt-dlp sans cookies: {e}")

    # Toutes les méthodes ont échoué
    error_msg = "Échec de téléchargement après 3 tentatives:\n" + "\n".join(f"  - {err}" for err in errors)
    raise Exception(error_msg)
