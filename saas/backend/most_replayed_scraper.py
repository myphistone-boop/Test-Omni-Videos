"""
Most Replayed Moments Scraper
Extrait les moments les plus visionnés d'une vidéo YouTube via Playwright
"""

import os
import json
import time
import random
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright


def parse_netscape_cookies(cookie_file: str):
    """Parse un fichier Netscape cookies.txt et retourne une liste de cookies pour Playwright"""
    cookies = []

    if not os.path.exists(cookie_file):
        print(f"❌ Fichier cookie introuvable : {cookie_file}")
        return cookies

    with open(cookie_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Ignorer les commentaires et lignes vides
            if not line or line.startswith('#'):
                continue

            # Format Netscape : domain, flag, path, secure, expiration, name, value
            try:
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain, flag, path, secure, expiration, name, value = parts[:7]

                    cookie = {
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': path,
                        'expires': int(expiration) if expiration != '0' else -1,
                        'httpOnly': False,
                        'secure': secure == 'TRUE',
                        'sameSite': 'None' if secure == 'TRUE' else 'Lax'
                    }
                    cookies.append(cookie)
            except Exception as e:
                print(f"⚠️  Erreur parsing ligne cookie : {e}")
                continue

    return cookies


def get_most_replayed_moments(video_url: str, cookie_file: str = None, headless: bool = True):
    """
    Récupère les moments les plus replays d'une vidéo YouTube

    Args:
        video_url: URL de la vidéo YouTube
        cookie_file: Chemin vers le fichier cookie (optionnel)
        headless: Mode headless (défaut: True)

    Returns:
        list[dict]: Liste des moments avec timestamps
        [
            {'start': 10.5, 'end': 25.3, 'score': 0.85},
            {'start': 120.0, 'end': 145.2, 'score': 0.92},
            ...
        ]
        None si échec
    """
    print("\n" + "=" * 70)
    print(f"🎬 MOST REPLAYED SCRAPER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"🔗 URL: {video_url}")
    print(f"🍪 Cookie: {cookie_file if cookie_file else 'Aucun'}")
    print(f"🎭 Headless: {headless}")
    print("")

    try:
        with sync_playwright() as p:
            print("🚀 [STEP 1] Lancement du navigateur...")

            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            print("✅ Navigateur lancé")

            print("🌐 [STEP 2] Création du contexte...")
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='fr-FR',
            )

            # Charger les cookies si disponibles
            if cookie_file and os.path.exists(cookie_file):
                print("🍪 [STEP 3] Chargement des cookies...")
                cookies = parse_netscape_cookies(cookie_file)
                if cookies:
                    context.add_cookies(cookies)
                    print(f"✅ {len(cookies)} cookies injectés")
                else:
                    print("⚠️  Aucun cookie chargé, continuation sans cookies")
            else:
                print("⚠️  [STEP 3] Pas de cookies, continuation en mode public")

            print("📄 [STEP 4] Ouverture de la page YouTube...")
            page = context.new_page()

            # Aller sur la vidéo
            page.goto(video_url, wait_until='domcontentloaded', timeout=30000)
            print("✅ Page chargée")

            # Attendre que le player se charge
            print("⏳ [STEP 5] Attente du chargement du player...")
            wait_time = random.randint(3, 5)
            time.sleep(wait_time)

            print("🔍 [STEP 6] Extraction des données YouTube...")

            # Récupérer ytInitialPlayerResponse (contient les heatmap data)
            player_response = page.evaluate('''() => {
                try {
                    return window.ytInitialPlayerResponse || null;
                } catch(e) {
                    return null;
                }
            }''')

            # Récupérer ytInitialData (données additionnelles)
            initial_data = page.evaluate('''() => {
                try {
                    return window.ytInitialData || null;
                } catch(e) {
                    return null;
                }
            }''')

            print("📊 [STEP 7] Parsing des moments les plus replays...")

            moments = []

            # Parser les heatmap markers (YouTube stocke ça dans playerResponse)
            if player_response:
                try:
                    # Chercher dans videoDetails
                    video_details = player_response.get('videoDetails', {})
                    video_title = video_details.get('title', 'Unknown')
                    duration = int(video_details.get('lengthSeconds', 0))

                    print(f"   📹 Titre: {video_title}")
                    print(f"   ⏱️  Durée: {duration}s")

                    # Chercher les heatmap markers
                    # Peut être dans : playerResponse.playerConfig.decoratedPlayerBarRenderer.decoratedPlayerBarRenderer.playerBar.multiMarkersPlayerBarRenderer.markersMap
                    decorations = player_response.get('playerConfig', {}).get('decoratedPlayerBarRenderer', {})
                    player_bar = decorations.get('decoratedPlayerBarRenderer', {}).get('playerBar', {})
                    multi_markers = player_bar.get('multiMarkersPlayerBarRenderer', {})
                    markers_map = multi_markers.get('markersMap', [])

                    print(f"   🔍 Markers trouvés : {len(markers_map)} catégories")

                    for marker_category in markers_map:
                        # Chercher spécifiquement "HEATMAP"
                        key = marker_category.get('key', '')

                        if 'HEATMAP' in key or 'MOST_REPLAYED' in key:
                            print(f"   ✅ Heatmap trouvée dans : {key}")

                            # Extraire les markers
                            value = marker_category.get('value', {})
                            heatmap = value.get('heatmap', {})
                            heatmap_renderer = heatmap.get('heatMapRenderer', {}) or heatmap.get('heatmapRenderer', {})
                            heat_markers = heatmap_renderer.get('heatMarkers', [])

                            print(f"   📍 {len(heat_markers)} marqueurs de chaleur trouvés")

                            for marker in heat_markers:
                                # marker contient : timeRangeStartMillis, heatMarkerRenderer
                                start_ms = marker.get('timeRangeStartMillis', 0)
                                heat_marker_renderer = marker.get('heatMarkerRenderer', {})
                                duration_ms = heat_marker_renderer.get('markerDurationMillis', 0)
                                heat_marker_intensity = heat_marker_renderer.get('heatMarkerIntensityScoreNormalized', 0)

                                start_sec = int(start_ms) / 1000.0
                                end_sec = start_sec + (int(duration_ms) / 1000.0)
                                score = float(heat_marker_intensity)

                                moments.append({
                                    'start': start_sec,
                                    'end': end_sec,
                                    'score': score
                                })

                                print(f"      • {start_sec:.1f}s - {end_sec:.1f}s (score: {score:.2f})")

                except Exception as e:
                    print(f"   ⚠️  Erreur parsing playerResponse: {e}")

            # Fermer
            print("🔒 [STEP 8] Fermeture du navigateur...")
            page.close()
            context.close()
            browser.close()

            print("")
            print("=" * 70)
            if moments:
                print(f"✅ SUCCÈS : {len(moments)} moments trouvés")
                # Trier par score décroissant
                moments.sort(key=lambda x: x['score'], reverse=True)
                print(f"🏆 Meilleur moment : {moments[0]['start']:.1f}s - {moments[0]['end']:.1f}s (score: {moments[0]['score']:.2f})")
            else:
                print("⚠️  AUCUN moment trouvé")
                print("💡 Raisons possibles :")
                print("   - La vidéo n'a pas assez de vues")
                print("   - YouTube n'a pas généré de heatmap pour cette vidéo")
                print("   - La structure des données YouTube a changé")
            print("=" * 70)
            print("")

            return moments if moments else None

    except Exception as e:
        print("")
        print("=" * 70)
        print("❌ ÉCHEC")
        print("=" * 70)
        print(f"Erreur : {str(e)}")
        print("")
        return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Most Replayed Moments Scraper')
    parser.add_argument('url', type=str, help='URL de la vidéo YouTube')
    parser.add_argument('--cookie-file', type=str, help='Chemin vers le fichier cookie')
    parser.add_argument('--headless', action='store_true', help='Mode headless')

    args = parser.parse_args()

    moments = get_most_replayed_moments(
        video_url=args.url,
        cookie_file=args.cookie_file,
        headless=args.headless
    )

    if moments:
        print("\n📊 Résultats JSON :")
        print(json.dumps(moments, indent=2))
    else:
        print("\n❌ Aucun résultat")
