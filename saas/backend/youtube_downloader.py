"""
YouTube downloader pour le backend SaaS
Télécharge des vidéos YouTube via yt-dlp avec Cookie Pool centralisé
"""

import yt_dlp
import os
import json
import asyncio
from pathlib import Path

# Import Cookie Pool Manager
try:
    from cookie_pool_manager import get_cookie_for_request, record_request_result
    COOKIE_POOL_AVAILABLE = True
except ImportError:
    print("⚠️  Cookie Pool Manager non disponible (import échoué)")
    COOKIE_POOL_AVAILABLE = False

# Import Interactive Cookie Capture
try:
    from interactive_cookie_capture import InteractiveCookieCapture
    INTERACTIVE_CAPTURE_AVAILABLE = True
except ImportError:
    print("⚠️  Interactive Cookie Capture non disponible (import échoué)")
    INTERACTIVE_CAPTURE_AVAILABLE = False


def get_cookies_interactively(account_name: str = "user") -> str:
    """
    Déclenche la capture interactive de cookies YouTube

    Args:
        account_name: Nom du compte pour sauvegarder les cookies

    Returns:
        str: Chemin du fichier cookies capturé
    """
    if not INTERACTIVE_CAPTURE_AVAILABLE:
        raise Exception(
            "Interactive Cookie Capture non disponible. "
            "Vérifiez que interactive_cookie_capture.py est présent."
        )

    print("\n" + "="*70)
    print("🔐 COOKIES REQUIS POUR CONTINUER")
    print("="*70)
    print("\n📋 Vous devez vous connecter à YouTube pour continuer.")
    print("   Un navigateur va s'ouvrir automatiquement.\n")

    # Créer le capturer et lancer la capture
    capturer = InteractiveCookieCapture()
    cookies_path = asyncio.run(capturer.capture_cookies(account_name))

    return cookies_path


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
    Télécharge une vidéo YouTube avec Cookie Pool automatique

    Stratégie intelligente:
    - Si cookies_path fourni → utilise ces cookies (priorité)
    - Sinon → utilise le Cookie Pool centralisé
    - Si Pool vide → erreur explicite

    Args:
        url: URL de la vidéo YouTube
        output_path: Chemin complet où sauvegarder la vidéo
        cookies_path: Chemin vers fichier cookies.txt (optionnel)

    Returns:
        str: Chemin du fichier téléchargé

    Raises:
        Exception: Si pas de cookies disponibles ou échec téléchargement
    """

    # Si cookies fournis explicitement, les utiliser
    if cookies_path and Path(cookies_path).exists():
        print(f"🔑 Utilisation des cookies fournis: {cookies_path}")
        return download_with_ytdlp(url, output_path, cookies_path)

    # Sinon, utiliser le Cookie Pool
    if COOKIE_POOL_AVAILABLE:
        pool_cookies = get_cookie_for_request()

        if pool_cookies:
            print(f"🔄 Utilisation du Cookie Pool: {Path(pool_cookies).name}")

            try:
                # Télécharger avec les cookies du pool
                result = download_with_ytdlp(url, output_path, pool_cookies)

                # Enregistrer le succès
                record_request_result(pool_cookies, success=True)

                return result

            except Exception as e:
                # Enregistrer l'échec
                error_msg = str(e)
                record_request_result(pool_cookies, success=False, error_msg=error_msg)
                raise
        else:
            print("⚠️  Cookie Pool saturé ou vide")

    # Fallback sur capture interactive
    if INTERACTIVE_CAPTURE_AVAILABLE:
        print("\n🔄 Aucun cookie disponible dans le pool")
        print("   → Déclenchement de la capture interactive...\n")

        try:
            cookies_path = get_cookies_interactively()
            print(f"\n✅ Cookies capturés: {cookies_path}")
            print("🔄 Nouvelle tentative de téléchargement...\n")

            return download_with_ytdlp(url, output_path, cookies_path)

        except Exception as e:
            print(f"\n❌ Erreur lors de la capture interactive: {e}")
            raise

    # Aucun cookie disponible et pas de capture interactive
    raise Exception(
        "Aucun cookie YouTube disponible. "
        "Le Cookie Pool est vide ou saturé. "
        "Attendez quelques minutes ou configurez le pool: /home/shorts/cookie_pool/"
    )


def download_youtube_subtitles_with_ytdlp(url: str, language: str = "fr", cookies_path: str = None):
    """
    Fallback: Télécharge les sous-titres YouTube via yt-dlp (plus robuste)

    Args:
        url: URL YouTube
        language: Code langue (fr, en, etc.)
        cookies_path: Chemin cookies (optionnel)

    Returns:
        list[dict]: Liste de mots avec timestamps au format Whisper
        None: Si pas de sous-titres disponibles
    """

    print(f"🔄 Tentative via yt-dlp...")

    cookies_file = cookies_path if cookies_path and Path(cookies_path).exists() else None

    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [language, 'en'],
        'subtitlesformat': 'json3',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookies_file,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})
            all_subs = {**automatic_captions, **subtitles}

            if not all_subs:
                print("❌ yt-dlp: Aucun sous-titre disponible")
                return None

            # Essayer plusieurs variantes de langues
            lang_variants = [language]
            if language == 'fr':
                lang_variants.extend(['fr-FR', 'fr-CA'])
            elif language == 'en':
                lang_variants.extend(['en-US', 'en-GB'])
            lang_variants.append('en')

            print(f"🔍 yt-dlp: Langues disponibles: {list(all_subs.keys())}")

            for lang in lang_variants:
                if lang in all_subs:
                    print(f"✅ yt-dlp: Sous-titres trouvés en '{lang}'")

                    for sub_format in all_subs[lang]:
                        if sub_format.get('ext') == 'json3':
                            sub_url = sub_format['url']

                            try:
                                import urllib.request
                                with urllib.request.urlopen(sub_url, timeout=10) as response:
                                    content = response.read().decode('utf-8')

                                    if not content.strip().startswith('{'):
                                        print(f"⚠️  yt-dlp: Réponse invalide pour '{lang}'")
                                        continue

                                    sub_data = json.loads(content)
                                    words = parse_youtube_subtitles_to_whisper(sub_data)

                                    if words and len(words) > 0:
                                        print(f"✅ yt-dlp: {len(words)} mots extraits!")
                                        return words

                            except Exception as e:
                                print(f"❌ yt-dlp: Erreur pour '{lang}': {e}")
                                continue

            print("❌ yt-dlp: Aucun sous-titre valide trouvé")
            return None

    except Exception as e:
        print(f"❌ yt-dlp: Erreur globale: {e}")
        return None


def download_youtube_subtitles(url: str, language: str = "fr", cookies_path: str = None):
    """
    Télécharge les sous-titres YouTube DIRECTEMENT via l'API (ULTRA-RAPIDE!)

    Stratégie intelligente:
    - Si cookies_path fourni → utilise ces cookies
    - Sinon → utilise le Cookie Pool centralisé
    - Enregistre succès/échec dans le pool

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

    # Utiliser Cookie Pool si pas de cookies fournis
    using_pool = False
    if not cookies_path and COOKIE_POOL_AVAILABLE:
        cookies_path = get_cookie_for_request()
        using_pool = True
        if cookies_path:
            print(f"🔄 Utilisation du Cookie Pool: {Path(cookies_path).name}")

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
        # Essayer d'abord les sous-titres manuels, puis auto-générés
        for subtitle_type in ['manual', 'auto']:
            try:
                print(f"\n{'='*60}")
                print(f"🔍 [STEP 1] Essai langue '{lang}' - Type: {subtitle_type}")
                print(f"{'='*60}")

                # URL directe de l'API YouTube timedtext
                # fmt=json3 donne le format avec timestamps mot par mot
                # kind=asr pour les sous-titres auto-générés
                if subtitle_type == 'auto':
                    timedtext_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang={lang}&fmt=json3&kind=asr"
                    print(f"   [STEP 1.1] URL construite (AUTO-GÉNÉRÉS): {timedtext_url}")
                else:
                    timedtext_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang={lang}&fmt=json3"
                    print(f"   [STEP 1.1] URL construite (MANUELS): {timedtext_url}")

                # Créer une requête avec cookies si disponibles
                print(f"   [STEP 1.2] Création de la requête HTTP...")
                req = urllib.request.Request(timedtext_url)

                # Ajouter des headers pour simuler un navigateur réel
                print(f"   [STEP 1.3] Ajout des headers navigateur...")
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                req.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
                req.add_header('Accept-Language', 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7')
                req.add_header('Referer', f'https://www.youtube.com/watch?v={video_id}')
                print(f"   [STEP 1.4] Headers ajoutés ✓")

                # Ajouter les cookies si disponibles
                if cookies_path and Path(cookies_path).exists():
                    print(f"   [STEP 1.5] Chargement des cookies depuis: {cookies_path}")
                    # Lire les cookies depuis le fichier Netscape
                    cookie_jar = http.cookiejar.MozillaCookieJar(cookies_path)
                    cookie_jar.load(ignore_discard=True, ignore_expires=True)
                    print(f"   [STEP 1.6] {len(cookie_jar)} cookies chargés")

                    # Créer un opener avec les cookies
                    print(f"   [STEP 1.7] Envoi de la requête avec cookies...")
                    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
                    response = opener.open(req, timeout=10)
                else:
                    print(f"   [STEP 1.5] Pas de cookies - envoi requête sans authentification...")
                    response = urllib.request.urlopen(req, timeout=10)

                print(f"   [STEP 2] Requête envoyée - Code HTTP: {response.getcode()}")

                # Lire la réponse
                print(f"   [STEP 3] Lecture de la réponse...")
                response_text = response.read().decode('utf-8')
                print(f"   [STEP 3.1] Réponse reçue - Taille: {len(response_text)} caractères")

                # Debug: afficher le début de la réponse
                print(f"   [STEP 3.2] Premiers 100 chars: {response_text[:100]}")

                # Vérifier que c'est bien du JSON
                print(f"   [STEP 4] Validation format JSON...")
                if not response_text or not response_text.strip().startswith('{'):
                    print(f"   [STEP 4.1] ❌ ÉCHEC - Pas du JSON pour '{lang}' ({subtitle_type})")
                    print(f"   [STEP 4.2] Type réponse: {type(response_text)}, Commence par: '{response_text[:50]}'")
                    continue

                print(f"   [STEP 4.3] ✓ Format JSON valide")

                # Parser le JSON
                print(f"   [STEP 5] Parsing JSON...")
                sub_data = json.loads(response_text)
                print(f"   [STEP 5.1] ✓ JSON parsé - Clés: {list(sub_data.keys())}")

                # Vérifier que ce n'est pas vide
                print(f"   [STEP 6] Validation contenu...")
                if not sub_data or 'events' not in sub_data or not sub_data['events']:
                    print(f"   [STEP 6.1] ❌ ÉCHEC - Sous-titres vides pour '{lang}' ({subtitle_type})")
                    print(f"   [STEP 6.2] Contenu: {sub_data}")
                    continue

                print(f"   [STEP 6.3] ✓ {len(sub_data.get('events', []))} événements trouvés")

                print(f"   [STEP 7] Parsing au format Whisper...")
                # Parser au format Whisper
                words = parse_youtube_subtitles_to_whisper(sub_data)
                print(f"   [STEP 7.1] ✓ Parsing terminé")

                print(f"\n{'='*60}")
                print(f"✅✅✅ SUCCÈS: {len(words)} mots extraits ({subtitle_type})!")
                print(f"{'='*60}\n")

                # Enregistrer le succès dans le pool
                if using_pool and COOKIE_POOL_AVAILABLE:
                    record_request_result(cookies_path, success=True)

                return words

            except urllib.error.HTTPError as e:
                print(f"\n   [ERROR] HTTPError pour '{lang}' ({subtitle_type}):")
                print(f"   - Code: {e.code}")
                print(f"   - Raison: {e.reason}")
                if e.code == 404:
                    print(f"   - Signification: Pas de sous-titres {subtitle_type} disponibles")
                continue
            except json.JSONDecodeError as e:
                print(f"\n   [ERROR] JSONDecodeError pour '{lang}' ({subtitle_type}):")
                print(f"   - Message: {e}")
                print(f"   - Position: ligne {e.lineno}, col {e.colno}")
                continue
            except Exception as e:
                print(f"\n   [ERROR] Exception pour '{lang}' ({subtitle_type}):")
                print(f"   - Type: {type(e).__name__}")
                print(f"   - Message: {e}")
                import traceback
                print(f"   - Traceback:")
                traceback.print_exc()
                continue

    print("\n❌ API directe a échoué pour toutes les langues testées")
    print(f"   Langues essayées: {lang_variants}")
    print("\n🔄 FALLBACK: Tentative avec yt-dlp (plus lent mais plus fiable)...\n")

    # FALLBACK: Utiliser yt-dlp si l'API directe échoue
    try:
        result = download_youtube_subtitles_with_ytdlp(url, language, cookies_path)

        # Si yt-dlp a réussi, enregistrer le succès
        if result and using_pool and COOKIE_POOL_AVAILABLE:
            record_request_result(cookies_path, success=True)

        return result

    except Exception as e:
        print(f"❌ Fallback yt-dlp a également échoué: {e}")

        # Enregistrer l'échec dans le pool
        if using_pool and COOKIE_POOL_AVAILABLE:
            record_request_result(cookies_path, success=False,
                                  error_msg="API directe et yt-dlp ont échoué")

        # Dernière tentative: capture interactive (si pas déjà fait avec cookies)
        if INTERACTIVE_CAPTURE_AVAILABLE and not cookies_path:
            print("\n🔄 Dernière tentative: capture interactive de cookies...")

            try:
                new_cookies_path = get_cookies_interactively()
                print(f"\n✅ Cookies capturés: {new_cookies_path}")
                print("🔄 Nouvelle tentative avec yt-dlp...\n")

                # Retry with the new cookies
                result = download_youtube_subtitles_with_ytdlp(url, language, new_cookies_path)

                if result:
                    print(f"✅ Succès avec cookies interactifs!")
                    return result
                else:
                    print(f"❌ Échec même avec cookies interactifs")

            except Exception as capture_error:
                print(f"\n❌ Erreur lors de la capture interactive: {capture_error}")

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
