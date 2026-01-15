"""
YouTube downloader pour le backend SaaS
Télécharge des vidéos YouTube via yt-dlp SANS cookies (mode public)
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
    Télécharge une vidéo YouTube (utilise automatiquement le cookie serveur si disponible)

    Stratégie:
    1. Si cookie serveur existe → l'utiliser
    2. Sinon → essayer sans cookies (mode public)
    3. Si échec → message clair

    Args:
        url: URL de la vidéo YouTube
        output_path: Chemin complet où sauvegarder la vidéo
        cookies_path: Chemin vers fichier cookies.txt (optionnel)

    Returns:
        str: Chemin du fichier téléchargé

    Raises:
        Exception: Si téléchargement échoue
    """

    # Si pas de cookies_path fourni, chercher le cookie serveur
    if cookies_path is None:
        server_cookie = "/home/shorts/cookies/account_1.txt"
        if os.path.exists(server_cookie):
            cookies_path = server_cookie
            print("🍪 Cookie serveur trouvé et utilisé automatiquement")
        else:
            print("🎬 Aucun cookie serveur, tentative en mode public...")

    try:
        # Télécharger avec le cookie (si disponible) ou sans
        return download_with_ytdlp(url, output_path, cookies_path=cookies_path)

    except Exception as e:
        error_msg = str(e)

        # Vérifier si c'est une erreur de détection bot
        if "Sign in" in error_msg or "bot" in error_msg.lower():
            if cookies_path is None:
                raise Exception(
                    "⚠️ YouTube a détecté un comportement automatisé. "
                    "Cette vidéo nécessite des cookies YouTube. "
                    "Uploadez un cookie via l'interface pour continuer."
                )
            else:
                raise Exception(
                    "⚠️ YouTube a détecté un comportement automatisé même avec cookies. "
                    "Le cookie est peut-être expiré ou invalide. "
                    "Uploadez un nouveau cookie via l'interface."
                )

        # Autre erreur
        raise Exception(f"Échec du téléchargement: {error_msg}")


def download_youtube_subtitles(url: str, language: str = "fr", cookies_path: str = None):
    """
    Télécharge les sous-titres YouTube DIRECTEMENT via l'API (ULTRA-RAPIDE!)

    Utilise automatiquement le cookie serveur si disponible

    Args:
        url: URL YouTube
        language: Code langue (fr, en, etc.)
        cookies_path: Chemin cookies (optionnel)

    Returns:
        list[dict]: Liste de mots avec timestamps au format Whisper
                    [{'word': 'bonjour', 'start': 0.5, 'end': 1.2}, ...]
        None: Si pas de sous-titres disponibles
    """

    # Si pas de cookies_path fourni, chercher le cookie serveur
    if cookies_path is None:
        server_cookie = "/home/shorts/cookies/account_1.txt"
        if os.path.exists(server_cookie):
            cookies_path = server_cookie
            print("🍪 Cookie serveur trouvé pour les sous-titres")

    print(f"🎬 Récupération DIRECTE des sous-titres YouTube...")
    print(f"   URL: {url}")
    print(f"   Langue: {language}")
    print(f"   Mode: {'AVEC cookies' if cookies_path else 'SANS cookies (public)'}")

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

    print("\n" + "="*70)
    print("❌ AUCUN SOUS-TITRE TROUVÉ")
    print("="*70)
    print(f"📝 Langue demandée: {language}")
    print(f"🔍 Variantes testées: {', '.join(lang_variants)}")
    print(f"🎯 Types testés: manuel + auto-généré")
    print("")
    print("💡 Raisons possibles:")
    print("   • La vidéo n'a pas de sous-titres dans cette langue")
    print("   • Les sous-titres sont désactivés par le créateur")
    print("   • La vidéo est trop récente (sous-titres pas encore générés)")
    print("   • La vidéo est privée/restreinte")
    print("")
    if language == 'fr':
        print("💬 Message utilisateur:")
        print("   ⚠️ Aucun sous-titre français trouvé pour cette vidéo.")
        print("   Les sous-titres YouTube ne sont pas disponibles en français.")
        print("   Vous pouvez réessayer avec une autre vidéo ou utiliser le mode Whisper (payant).")
    else:
        print("💬 Message utilisateur:")
        print(f"   ⚠️ Aucun sous-titre {language.upper()} trouvé pour cette vidéo.")
        print(f"   Les sous-titres YouTube ne sont pas disponibles dans cette langue.")
    print("="*70 + "\n")

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
