"""
Debug YouTube Data Structure
Extrait et affiche ytInitialPlayerResponse pour analyser la structure
"""

import os
import json
from pathlib import Path
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


def debug_youtube_data(video_url: str, cookie_file: str = None):
    """Extrait et sauvegarde ytInitialPlayerResponse"""

    print("=" * 70)
    print("🔍 DEBUG YOUTUBE DATA STRUCTURE")
    print("=" * 70)
    print(f"URL: {video_url}")
    print("")

    with sync_playwright() as p:
        print("🚀 Lancement du navigateur...")
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='fr-FR',
        )

        if cookie_file and os.path.exists(cookie_file):
            print(f"🍪 Chargement des cookies...")
            cookies = parse_netscape_cookies(cookie_file)
            if cookies:
                context.add_cookies(cookies)
                print(f"✅ {len(cookies)} cookies injectés")

        page = context.new_page()
        print("📄 Chargement de la page...")
        page.goto(video_url, wait_until='domcontentloaded', timeout=30000)

        import time
        time.sleep(5)  # Attendre que tout se charge

        print("📊 Extraction de ytInitialPlayerResponse...")
        player_response = page.evaluate('() => window.ytInitialPlayerResponse')

        print("📊 Extraction de ytInitialData...")
        initial_data = page.evaluate('() => window.ytInitialData')

        # Sauvegarder dans des fichiers
        output_file_pr = "/tmp/ytInitialPlayerResponse.json"
        output_file_id = "/tmp/ytInitialData.json"

        if player_response:
            with open(output_file_pr, 'w', encoding='utf-8') as f:
                json.dump(player_response, f, indent=2, ensure_ascii=False)
            print(f"✅ ytInitialPlayerResponse sauvegardé : {output_file_pr}")
            print(f"   Taille: {len(json.dumps(player_response))} caractères")

            # Afficher les clés principales
            print(f"\n📋 Clés principales dans playerResponse:")
            for key in player_response.keys():
                print(f"   • {key}")

            # Chercher "heatmap" ou "marker" dans tout le JSON
            json_str = json.dumps(player_response).lower()
            if 'heatmap' in json_str:
                print(f"\n✅ Mot 'heatmap' trouvé dans playerResponse!")
            if 'marker' in json_str:
                print(f"✅ Mot 'marker' trouvé dans playerResponse!")
            if 'replayed' in json_str:
                print(f"✅ Mot 'replayed' trouvé dans playerResponse!")

        if initial_data:
            with open(output_file_id, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ ytInitialData sauvegardé : {output_file_id}")
            print(f"   Taille: {len(json.dumps(initial_data))} caractères")

            # Chercher dans initialData aussi
            json_str = json.dumps(initial_data).lower()
            if 'heatmap' in json_str:
                print(f"\n✅ Mot 'heatmap' trouvé dans initialData!")
            if 'marker' in json_str:
                print(f"✅ Mot 'marker' trouvé dans initialData!")
            if 'replayed' in json_str:
                print(f"✅ Mot 'replayed' trouvé dans initialData!")

        page.close()
        context.close()
        browser.close()

        print("\n" + "=" * 70)
        print("✅ DEBUG TERMINÉ")
        print("=" * 70)
        print(f"\nAnalyse les fichiers:")
        print(f"  cat {output_file_pr} | grep -i heatmap")
        print(f"  cat {output_file_pr} | grep -i marker")
        print(f"  cat {output_file_id} | grep -i heatmap")
        print("")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='URL YouTube')
    parser.add_argument('--cookie-file', help='Fichier cookies')
    args = parser.parse_args()

    debug_youtube_data(args.url, args.cookie_file)
