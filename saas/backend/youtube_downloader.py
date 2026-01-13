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
    Télécharge les sous-titres YouTube (auto-générés ou manuels)

    Args:
        url: URL YouTube
        language: Code langue (fr, en, etc.)
        cookies_path: Chemin cookies (optionnel)

    Returns:
        list[dict]: Liste de mots avec timestamps au format Whisper
                    [{'word': 'bonjour', 'start': 0.5, 'end': 1.2}, ...]
        None: Si pas de sous-titres disponibles
    """

    print(f"🎬 Tentative de récupération des sous-titres YouTube...")
    print(f"   URL: {url}")
    print(f"   Langue demandée: {language}")

    cookies_file = cookies_path if cookies_path and Path(cookies_path).exists() else None
    print(f"   Cookies: {cookies_file or 'AUCUN'}")

    ydl_opts = {
        'skip_download': True,  # Ne pas télécharger la vidéo
        'writesubtitles': True,  # Sous-titres manuels
        'writeautomaticsub': True,  # Sous-titres auto-générés
        'subtitleslangs': [language, 'en'],  # Langues préférées
        'subtitlesformat': 'json3',  # Format JSON avec timestamps précis
        'quiet': False,  # MODE DEBUG: Verbose!
        'no_warnings': False,  # MODE DEBUG: Montrer les warnings
        'cookiefile': cookies_file,
    }

    print(f"   Options yt-dlp: {ydl_opts}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("\n📥 Extraction des infos vidéo...")
            info = ydl.extract_info(url, download=False)

            # Vérifier si des sous-titres sont disponibles
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            print(f"\n📋 DEBUG - Sous-titres disponibles:")
            print(f"   Manuels: {list(subtitles.keys())}")
            print(f"   Auto-générés: {list(automatic_captions.keys())}")

            # Priorité: sous-titres manuels > sous-titres auto
            all_subs = {**automatic_captions, **subtitles}

            if not all_subs:
                print("❌ AUCUN sous-titre disponible (ni manuel ni auto-généré)")
                print(f"   Info vidéo: title={info.get('title', 'N/A')}, id={info.get('id', 'N/A')}")
                return None

            print(f"✅ Total langues disponibles: {list(all_subs.keys())}")

            # Chercher dans l'ordre: langue demandée, puis anglais
            # Recherche FLEXIBLE: accepte fr, fr-CA, fr-FR, etc.
            for search_lang in [language, 'en']:
                print(f"\n🔍 Recherche sous-titres en '{search_lang}'...")

                # Chercher une correspondance exacte OU une variante (fr-CA pour fr)
                found_lang = None

                # 1. Essayer correspondance exacte
                if search_lang in all_subs:
                    found_lang = search_lang
                    print(f"   ✅ Trouvé exact: '{found_lang}'")
                else:
                    # 2. Chercher une variante (ex: fr-CA, fr-FR pour "fr")
                    for available_lang in all_subs.keys():
                        if available_lang.startswith(search_lang + '-'):
                            found_lang = available_lang
                            print(f"   ✅ Trouvé variante: '{found_lang}' pour '{search_lang}'")
                            break

                if found_lang:
                    print(f"   ✅ Formats disponibles: {[s.get('ext') for s in all_subs[found_lang]]}")

                    # Récupérer les sous-titres au format json3
                    for sub_format in all_subs[found_lang]:
                        print(f"   📝 Test format: {sub_format.get('ext')}")
                        if sub_format.get('ext') == 'json3':
                            print(f"   ✅ Format json3 trouvé! URL: {sub_format['url'][:100]}...")

                            # Télécharger le fichier JSON
                            sub_url = sub_format['url']

                            # Utiliser yt-dlp pour télécharger le contenu
                            import urllib.request
                            print(f"   📥 Téléchargement du JSON...")
                            with urllib.request.urlopen(sub_url) as response:
                                sub_data = json.loads(response.read().decode('utf-8'))

                            print(f"   ✅ JSON téléchargé, parsing...")
                            # Parser au format Whisper
                            words = parse_youtube_subtitles_to_whisper(sub_data)
                            print(f"   ✅✅✅ {len(words)} mots extraits des sous-titres YouTube!")
                            return words
                else:
                    print(f"   ❌ Pas de sous-titres en '{search_lang}' (ni variantes)")

            print("\n❌ ERREUR: Format json3 non disponible dans aucune langue")
            print(f"   Langues disponibles: {list(all_subs.keys())}")
            return None

    except Exception as e:
        print(f"❌❌❌ EXCEPTION lors de la récupération des sous-titres:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {e}")
        import traceback
        print(f"   Stack trace:")
        traceback.print_exc()
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
