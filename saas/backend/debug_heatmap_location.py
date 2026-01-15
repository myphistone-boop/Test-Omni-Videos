"""
Debug script pour trouver où se cache exactement le heatmap "Most Replayed"
"""

import os
import time
from playwright.sync_api import sync_playwright


def parse_netscape_cookies(cookie_file: str):
    """Parse un fichier Netscape cookies.txt"""
    cookies = []
    if not os.path.exists(cookie_file):
        return cookies

    with open(cookie_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
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
            except:
                continue
    return cookies


def debug_heatmap_location(video_url: str, cookie_file: str = None, headless: bool = False):
    """
    Inspecte la page YouTube pour trouver où se cache le heatmap
    """
    print("\n" + "=" * 80)
    print("🔍 DEBUG HEATMAP LOCATION")
    print("=" * 80)
    print(f"URL: {video_url}")
    print("")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )

        if cookie_file and os.path.exists(cookie_file):
            cookies = parse_netscape_cookies(cookie_file)
            if cookies:
                context.add_cookies(cookies)
                print(f"✅ {len(cookies)} cookies chargés\n")

        page = context.new_page()
        page.goto(video_url, wait_until='domcontentloaded', timeout=30000)

        print("⏳ Attente du chargement complet...")
        time.sleep(5)

        # Stratégie 1: Chercher tous les SVG sur la page principale
        print("\n" + "=" * 80)
        print("📊 STRATÉGIE 1: Tous les SVG sur la page principale")
        print("=" * 80)

        all_svgs = page.evaluate('''() => {
            const svgs = Array.from(document.querySelectorAll('svg'));
            return svgs.map((svg, idx) => ({
                index: idx,
                classes: svg.className.baseVal || svg.className,
                id: svg.id,
                parent: svg.parentElement?.tagName,
                hasPath: svg.querySelector('path') !== null,
                pathCount: svg.querySelectorAll('path').length
            }));
        }''')

        print(f"Trouvé {len(all_svgs)} SVG sur la page principale:")
        for svg in all_svgs:
            print(f"  #{svg['index']}: classes='{svg['classes']}' id='{svg['id']}' parent={svg['parent']} paths={svg['pathCount']}")

        # Stratégie 2: Chercher dans l'iframe du player
        print("\n" + "=" * 80)
        print("📺 STRATÉGIE 2: Chercher dans l'iframe du player YouTube")
        print("=" * 80)

        iframes = page.frames
        print(f"Trouvé {len(iframes)} iframe(s) sur la page")

        for i, frame in enumerate(iframes):
            print(f"\n  iframe #{i}: {frame.url[:100]}...")
            try:
                svgs_in_frame = frame.evaluate('''() => {
                    const svgs = Array.from(document.querySelectorAll('svg'));
                    return svgs.map((svg, idx) => ({
                        index: idx,
                        classes: svg.className.baseVal || svg.className,
                        id: svg.id,
                        parent: svg.parentElement?.tagName,
                        hasPath: svg.querySelector('path') !== null,
                        pathCount: svg.querySelectorAll('path').length
                    }));
                }''')
                print(f"    → {len(svgs_in_frame)} SVG dans cette iframe")
                for svg in svgs_in_frame:
                    print(f"       #{svg['index']}: classes='{svg['classes']}' id='{svg['id']}' parent={svg['parent']} paths={svg['pathCount']}")
            except Exception as e:
                print(f"    → Erreur: {e}")

        # Stratégie 3: Hover et attendre
        print("\n" + "=" * 80)
        print("🖱️  STRATÉGIE 3: Hover sur la progress bar et attendre")
        print("=" * 80)

        try:
            # Trouver la progress bar
            progress_selectors = [
                '.ytp-progress-bar-container',
                '.ytp-progress-bar',
                '.html5-video-player .ytp-progress-bar',
                '#movie_player .ytp-progress-bar-container'
            ]

            for selector in progress_selectors:
                try:
                    print(f"  Essai du sélecteur: {selector}")
                    progress = page.locator(selector).first
                    if progress:
                        print(f"    ✅ Trouvé! Hover...")
                        progress.hover()
                        time.sleep(3)
                        print(f"    ✅ Hover effectué, attente 3s...")
                        break
                except Exception as e:
                    print(f"    ❌ Échec: {e}")
        except Exception as e:
            print(f"  ❌ Impossible de hover: {e}")

        # Stratégie 4: Chercher spécifiquement le heatmap après hover
        print("\n" + "=" * 80)
        print("🔥 STRATÉGIE 4: Chercher le heatmap après hover")
        print("=" * 80)

        heatmap_selectors = [
            'svg.ytp-heat-map-svg',
            '.ytp-heat-map-svg',
            'svg[class*="heat"]',
            'svg[class*="heatmap"]',
            '.ytp-progress-bar svg',
            '.ytp-progress-bar-container svg'
        ]

        for selector in heatmap_selectors:
            try:
                print(f"  Essai du sélecteur: {selector}")
                result = page.evaluate(f'''() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;
                    const path = el.querySelector('path');
                    return {{
                        found: true,
                        hasPath: path !== null,
                        pathD: path ? path.getAttribute('d')?.substring(0, 100) : null,
                        classes: el.className.baseVal || el.className
                    }};
                }}''')
                if result:
                    print(f"    ✅ TROUVÉ!")
                    print(f"       Classes: {result['classes']}")
                    print(f"       Has path: {result['hasPath']}")
                    if result['pathD']:
                        print(f"       Path (début): {result['pathD']}")
                else:
                    print(f"    ❌ Non trouvé")
            except Exception as e:
                print(f"    ❌ Erreur: {e}")

        # Stratégie 5: Dump tout le HTML du player
        print("\n" + "=" * 80)
        print("📝 STRATÉGIE 5: HTML du conteneur du player")
        print("=" * 80)

        try:
            player_html = page.evaluate('''() => {
                const player = document.querySelector('#movie_player') ||
                               document.querySelector('.html5-video-player');
                if (!player) return "Player non trouvé";

                // Chercher tous les éléments avec "heat" dans la classe
                const heatElements = Array.from(player.querySelectorAll('*'))
                    .filter(el => el.className &&
                            (el.className.toString().includes('heat') ||
                             el.className.toString().includes('replayed')));

                return heatElements.map(el => ({
                    tag: el.tagName,
                    classes: el.className.baseVal || el.className.toString(),
                    id: el.id,
                    children: el.children.length
                }));
            }''')

            if isinstance(player_html, list) and len(player_html) > 0:
                print(f"Trouvé {len(player_html)} éléments avec 'heat' ou 'replayed':")
                for el in player_html:
                    print(f"  <{el['tag']}> classe='{el['classes']}' id='{el['id']}' children={el['children']}")
            else:
                print(f"Aucun élément trouvé avec 'heat' ou 'replayed'")
        except Exception as e:
            print(f"Erreur: {e}")

        # Stratégie 6: Screenshot pour debug visuel
        print("\n" + "=" * 80)
        print("📸 STRATÉGIE 6: Screenshot")
        print("=" * 80)

        screenshot_path = "/tmp/youtube_heatmap_debug.png"
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"✅ Screenshot sauvegardé: {screenshot_path}")

        # Stratégie 7: Essayer de cliquer sur la vidéo et hover
        print("\n" + "=" * 80)
        print("🎬 STRATÉGIE 7: Interaction avec le player")
        print("=" * 80)

        try:
            # Cliquer sur la vidéo pour l'activer
            video = page.locator('video').first
            if video:
                print("  Clic sur la vidéo...")
                video.click()
                time.sleep(1)

                # Hover sur le player
                player = page.locator('#movie_player').first
                if player:
                    print("  Hover sur le player...")
                    player.hover()
                    time.sleep(2)

                    # Maintenant chercher le SVG
                    svg_after_interact = page.evaluate('''() => {
                        const svg = document.querySelector('svg.ytp-heat-map-svg') ||
                                    document.querySelector('.ytp-heat-map-svg') ||
                                    document.querySelector('#movie_player svg[class*="heat"]');
                        if (!svg) return null;
                        const path = svg.querySelector('path');
                        return {
                            found: true,
                            classes: svg.className.baseVal || svg.className,
                            pathD: path ? path.getAttribute('d') : null
                        };
                    }''')

                    if svg_after_interact:
                        print(f"  ✅ SVG TROUVÉ après interaction!")
                        print(f"     Classes: {svg_after_interact['classes']}")
                        if svg_after_interact['pathD']:
                            print(f"     Path (100 premiers cars): {svg_after_interact['pathD'][:100]}")
                    else:
                        print(f"  ❌ SVG toujours pas trouvé")
        except Exception as e:
            print(f"  ❌ Erreur interaction: {e}")

        print("\n" + "=" * 80)
        print("🔍 DEBUG TERMINÉ")
        print("=" * 80)
        print("")

        browser.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Debug Heatmap Location')
    parser.add_argument('url', type=str, help='URL de la vidéo YouTube')
    parser.add_argument('--cookie-file', type=str, help='Chemin vers le fichier cookie')
    parser.add_argument('--headless', action='store_true', help='Mode headless')

    args = parser.parse_args()

    debug_heatmap_location(
        video_url=args.url,
        cookie_file=args.cookie_file,
        headless=args.headless
    )
