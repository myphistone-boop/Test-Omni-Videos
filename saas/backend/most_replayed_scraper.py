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


def parse_svg_path(path_data: str):
    """
    Parse le path SVG du heatmap YouTube

    Args:
        path_data: Attribut 'd' du path SVG (ex: "M5.0,95.2 C...")

    Returns:
        list[(x, y)]: Liste de coordonnées
    """
    coordinates = []

    # Extraire tous les nombres du path
    import re
    numbers = re.findall(r'[-+]?\d*\.?\d+', path_data)

    # Grouper par paires (x, y)
    for i in range(0, len(numbers) - 1, 2):
        try:
            x = float(numbers[i])
            y = float(numbers[i + 1])
            coordinates.append((x, y))
        except:
            continue

    return coordinates


def get_most_replayed_moments(video_url: str, cookie_file: str = None, headless: bool = True):
    """
    Récupère les moments les plus replays d'une vidéo YouTube
    Méthode: Parse le SVG heatmap dans le DOM

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
            time.sleep(5)

            # Récupérer la durée de la vidéo
            print("📊 [STEP 6] Extraction des infos vidéo...")
            video_info = page.evaluate('''() => {
                const response = window.ytInitialPlayerResponse;
                if (!response) return null;
                return {
                    title: response.videoDetails?.title || 'Unknown',
                    duration: parseInt(response.videoDetails?.lengthSeconds || 0)
                };
            }''')

            if video_info:
                print(f"   📹 Titre: {video_info['title']}")
                print(f"   ⏱️  Durée: {video_info['duration']}s")
                video_duration = video_info['duration']
            else:
                print("   ⚠️  Impossible de récupérer les infos vidéo")
                video_duration = 0

            # Chercher le SVG heatmap dans le DOM
            print("🔍 [STEP 7] Interaction avec le player et recherche du heatmap...")

            # Stratégie d'interaction améliorée
            try:
                # 1. Cliquer sur la vidéo pour activer le player
                print("   → Clic sur la vidéo pour activer le player...")
                video = page.locator('video').first
                if video:
                    video.click()
                    time.sleep(1)
                    print("   ✅ Vidéo cliquée")

                # 2. Hover sur le player pour faire apparaître les contrôles
                print("   → Hover sur le player...")
                player = page.locator('#movie_player').first
                if player:
                    player.hover()
                    time.sleep(1.5)
                    print("   ✅ Hover sur le player effectué")

                # 3. Hover spécifiquement sur la progress bar
                print("   → Hover sur la barre de progression...")
                progress_selectors = [
                    '.ytp-progress-bar-container',
                    '.ytp-progress-bar',
                    '#movie_player .ytp-progress-bar-container'
                ]

                progress_found = False
                for selector in progress_selectors:
                    try:
                        progress = page.locator(selector).first
                        if progress:
                            progress.hover()
                            time.sleep(2)
                            print(f"   ✅ Hover effectué sur {selector}")
                            progress_found = True
                            break
                    except:
                        continue

                if not progress_found:
                    print("   ⚠️  Progress bar non trouvée, continuation quand même...")

            except Exception as e:
                print(f"   ⚠️  Erreur interaction: {e}")

            # Extraire le SVG path avec plusieurs stratégies
            print("📊 [STEP 8] Extraction du SVG path (essai de plusieurs méthodes)...")

            svg_path_data = None

            # Stratégie 1: Sélecteur classique
            svg_path_data = page.evaluate('''() => {
                const svg = document.querySelector('svg.ytp-heat-map-svg');
                if (!svg) return null;
                const path = svg.querySelector('path.ytp-heat-map-path') ||
                             svg.querySelector('path');
                return path ? path.getAttribute('d') : null;
            }''')

            if svg_path_data:
                print("   ✅ [Stratégie 1] SVG trouvé avec sélecteur classique")
            else:
                # Stratégie 2: Chercher n'importe quel SVG avec "heat" dans la classe
                print("   → [Stratégie 2] Recherche avec sélecteurs alternatifs...")
                svg_path_data = page.evaluate('''() => {
                    const selectors = [
                        'svg[class*="heat"]',
                        '.ytp-heat-map-svg',
                        '#movie_player svg[class*="heat"]',
                        '.ytp-progress-bar svg',
                        '.ytp-progress-bar-container svg'
                    ];

                    for (const selector of selectors) {
                        const svg = document.querySelector(selector);
                        if (svg) {
                            const path = svg.querySelector('path');
                            if (path) {
                                const d = path.getAttribute('d');
                                if (d && d.length > 50) {
                                    return d;
                                }
                            }
                        }
                    }
                    return null;
                }''')

                if svg_path_data:
                    print("   ✅ [Stratégie 2] SVG trouvé avec sélecteurs alternatifs")

            # Stratégie 3: Si toujours rien, chercher TOUS les SVG et filtrer
            if not svg_path_data:
                print("   → [Stratégie 3] Analyse de tous les SVG de la page...")
                svg_path_data = page.evaluate('''() => {
                    const allSvgs = Array.from(document.querySelectorAll('svg'));

                    for (const svg of allSvgs) {
                        const path = svg.querySelector('path');
                        if (path) {
                            const d = path.getAttribute('d');
                            // Le path du heatmap commence généralement par "M5" ou "M 5"
                            // et contient des courbes Bézier (C)
                            if (d && d.length > 100 && d.includes('C') &&
                                (d.startsWith('M5') || d.startsWith('M 5'))) {
                                return d;
                            }
                        }
                    }
                    return null;
                }''')

                if svg_path_data:
                    print("   ✅ [Stratégie 3] SVG trouvé par analyse de tous les paths")

            moments = []

            if svg_path_data:
                print(f"   ✅ SVG path trouvé ({len(svg_path_data)} caractères)")
                print(f"   📐 Début du path: {svg_path_data[:100]}...")

                # Parser les coordonnées
                print("🔢 [STEP 9] Parsing des coordonnées...")
                coordinates = parse_svg_path(svg_path_data)
                print(f"   ✅ {len(coordinates)} coordonnées extraites")

                if coordinates and video_duration > 0:
                    # Filtrer pour prendre seulement les points de données (x se termine par .0 ou .5)
                    # et convertir en moments
                    print("📊 [STEP 10] Conversion en moments...")

                    # Détecter les pics (y faible = intensité élevée car axe inversé)
                    threshold = 80  # Seulement les moments avec y < 80 (intensité > 20%)
                    peaks = []

                    for i, (x, y) in enumerate(coordinates):
                        # Convertir x en position temporelle (0-1)
                        time_position = (x - 5) / 1000 if x >= 5 else 0
                        # Convertir y en intensité (100-y car axe inversé)
                        intensity = (100 - y) / 100

                        # Ne garder que les pics significatifs
                        if y < threshold and time_position >= 0 and time_position <= 1:
                            timestamp = time_position * video_duration
                            peaks.append({
                                'timestamp': timestamp,
                                'intensity': intensity
                            })

                    print(f"   🔍 {len(peaks)} pics détectés (seuil: y < {threshold})")

                    # Grouper les pics consécutifs en segments
                    if peaks:
                        current_segment = None
                        min_gap = 5  # Secondes minimum entre segments

                        for peak in peaks:
                            if current_segment is None:
                                current_segment = {
                                    'start': peak['timestamp'],
                                    'end': peak['timestamp'],
                                    'max_intensity': peak['intensity']
                                }
                            elif peak['timestamp'] - current_segment['end'] <= min_gap:
                                # Étendre le segment
                                current_segment['end'] = peak['timestamp']
                                current_segment['max_intensity'] = max(
                                    current_segment['max_intensity'],
                                    peak['intensity']
                                )
                            else:
                                # Nouveau segment
                                if current_segment['end'] - current_segment['start'] >= 5:  # Au moins 5s
                                    moments.append({
                                        'start': current_segment['start'],
                                        'end': current_segment['end'],
                                        'score': current_segment['max_intensity']
                                    })
                                current_segment = {
                                    'start': peak['timestamp'],
                                    'end': peak['timestamp'],
                                    'max_intensity': peak['intensity']
                                }

                        # Ajouter le dernier segment
                        if current_segment and current_segment['end'] - current_segment['start'] >= 5:
                            moments.append({
                                'start': current_segment['start'],
                                'end': current_segment['end'],
                                'score': current_segment['max_intensity']
                            })

                    print(f"   ✅ {len(moments)} moments extraits")
                    for i, m in enumerate(moments[:5]):  # Afficher les 5 premiers
                        print(f"      • {m['start']:.1f}s - {m['end']:.1f}s (score: {m['score']:.2f})")

            else:
                print("   ❌ Aucun SVG heatmap trouvé après toutes les stratégies")
                print("")
                print("   💡 Debug: Analyse des SVG présents sur la page...")
                debug_info = page.evaluate('''() => {
                    const allSvgs = Array.from(document.querySelectorAll('svg'));
                    return {
                        totalSvgs: allSvgs.length,
                        svgsWithPaths: allSvgs.filter(s => s.querySelector('path')).length,
                        svgsInPlayer: Array.from(
                            (document.querySelector('#movie_player') || document.body)
                            .querySelectorAll('svg')
                        ).length
                    };
                }''')
                print(f"      • Total SVG sur la page: {debug_info['totalSvgs']}")
                print(f"      • SVG avec paths: {debug_info['svgsWithPaths']}")
                print(f"      • SVG dans le player: {debug_info['svgsInPlayer']}")
                print("")
                print("   💡 Raisons possibles:")
                print("      - La vidéo n'a pas assez de vues (généralement < 90k)")
                print("      - La vidéo est trop récente (< 5-7 jours)")
                print("      - YouTube n'a pas généré de heatmap pour cette vidéo")
                print("      - Le heatmap nécessite une interaction supplémentaire")
                print("")
                print("   🔧 Suggestion: Essayer le script de debug:")
                print("      venv/bin/python3 debug_heatmap_location.py \"URL\"")
                print("")

            # Fermer
            print("🔒 [STEP 11] Fermeture du navigateur...")
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
                print("   - La vidéo n'a pas assez de vues (< 90k)")
                print("   - La vidéo est trop récente (< 5-7 jours)")
                print("   - YouTube n'a pas généré de heatmap pour cette vidéo")
            print("=" * 70)
            print("")

            return moments if moments else None

    except Exception as e:
        print("")
        print("=" * 70)
        print("❌ ÉCHEC")
        print("=" * 70)
        print(f"Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
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
