"""
YouTube downloader pour le backend SaaS
Télécharge des vidéos YouTube via yt-dlp avec cookies utilisateur
"""

import yt_dlp
import os
import json
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
        'quiet': False,  # Verbose pour debug
        'no_warnings': False,
        'nocheckcertificate': True,
        'cookiefile': cookies_file if Path(cookies_file).exists() else None,
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


def download_youtube_subtitles(url: str, language: str = "fr", cookies_path: str = None):
    """
    Télécharge les sous-titres YouTube DIRECTEMENT via l'API (ULTRA-RAPIDE!)

    Args:
        url: URL YouTube
        language: Code langue (fr, en, etc.)
        cookies_path: Chemin cookies (optionnel)

    Returns:
        list[dict]: Liste de mots avec timestamps au format Whisper
                    [{'word': 'bonjour', 'start': 0.5, 'end': 1.2}, ...]
        None: Si pas de sous-titres disponibles
    """

    print(f"🎬 Récupération DIRECTE des sous-titres YouTube...")
    print(f"   URL: {url}")
    print(f"   Langue: {language}")

    # Extraire l'ID vidéo de l'URL
    import re
    video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
    if not video_id_match:
        print("❌ ID vidéo non trouvé dans l'URL")
        return None

    video_id = video_id_match.group(1)
    print(f"   ID vidéo: {video_id}")

    # Essayer plusieurs variantes de langue
    lang_variants = [language]
    if language == 'fr':
        lang_variants.extend(['fr-CA', 'fr-FR'])
    elif language == 'en':
        lang_variants.extend(['en-US', 'en-GB'])

    # Essayer d'abord sans variante, puis avec
    lang_variants.append('en')  # Fallback sur anglais

    import urllib.request
    import urllib.error
    import http.cookiejar

    for lang in lang_variants:
        try:
            # URL directe de l'API YouTube timedtext
            # fmt=json3 donne le format avec timestamps mot par mot
            timedtext_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang={lang}&fmt=json3"

            print(f"\n🔍 Essai langue '{lang}'...")
            print(f"   URL: {timedtext_url[:80]}...")

            # Créer une requête avec cookies si disponibles
            req = urllib.request.Request(timedtext_url)

            # Ajouter les cookies si disponibles
            if cookies_path and Path(cookies_path).exists():
                # Lire les cookies depuis le fichier Netscape
                cookie_jar = http.cookiejar.MozillaCookieJar(cookies_path)
                cookie_jar.load(ignore_discard=True, ignore_expires=True)

                # Créer un opener avec les cookies
                opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
                response = opener.open(req, timeout=10)
            else:
                response = urllib.request.urlopen(req, timeout=10)

            # Lire et parser le JSON
            sub_data = json.loads(response.read().decode('utf-8'))

            # Vérifier que ce n'est pas vide
            if not sub_data or 'events' not in sub_data or not sub_data['events']:
                print(f"   ❌ Sous-titres vides pour '{lang}'")
                continue

            print(f"   ✅ Sous-titres trouvés! Parsing...")

            # Parser au format Whisper
            words = parse_youtube_subtitles_to_whisper(sub_data)
            print(f"   ✅✅✅ {len(words)} mots extraits des sous-titres YouTube!")
            return words

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"   ❌ Pas de sous-titres en '{lang}' (404)")
            else:
                print(f"   ❌ Erreur HTTP {e.code} pour '{lang}'")
            continue
        except Exception as e:
            print(f"   ❌ Erreur pour '{lang}': {e}")
            continue

    print("\n❌ Aucun sous-titre trouvé dans aucune langue testée")
    print(f"   Langues essayées: {lang_variants}")
    return None


def parse_youtube_subtitles_to_whisper(sub_data):
    """
    Parse les sous-titres YouTube JSON3 au format Whisper

    Args:
        sub_data: Données JSON3 des sous-titres YouTube

    Returns:
        list[dict]: Format Whisper [{'word': 'mot', 'start': 0.5, 'end': 1.2}]
    """

    words = []

    # JSON3 contient 'events' avec timing mot par mot
    events = sub_data.get('events', [])

    for event in events:
        # Vérifier si l'event a des segments (mots)
        if 'segs' not in event:
            continue

        start_time = event.get('tStartMs', 0) / 1000.0  # Convertir ms en secondes

        for seg in event['segs']:
            # Certains segments sont juste des espaces/ponctuation
            if 'utf8' not in seg:
                continue

            text = seg['utf8'].strip()
            if not text or text in ['\n', ' ']:
                continue

            # Durée du segment (si disponible, sinon estimer)
            offset_ms = seg.get('tOffsetMs', 0)
            offset_sec = offset_ms / 1000.0

            word_start = start_time + offset_sec

            # Estimer la fin (YouTube ne donne pas toujours la durée exacte)
            # On utilise le début du mot suivant ou +0.3s par défaut
            word_end = word_start + 0.3

            words.append({
                'word': text,
                'start': word_start,
                'end': word_end
            })

    # Ajuster les 'end' en fonction du 'start' suivant
    for i in range(len(words) - 1):
        words[i]['end'] = min(words[i]['end'], words[i + 1]['start'])

    return words
