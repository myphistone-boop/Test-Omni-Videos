"""
Cookie Keeper - Maintien en vie des cookies YouTube
Visite YouTube régulièrement pour garder le cookie actif
"""

import os
import time
import random
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# Paths
COOKIE_FILE = Path("/home/shorts/cookies/account_1.txt")


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

    print(f"✅ {len(cookies)} cookies chargés depuis {cookie_file}")
    return cookies


def save_cookies_to_netscape(cookies, output_file: str):
    """Sauvegarde les cookies au format Netscape"""
    with open(output_file, 'w') as f:
        f.write('# Netscape HTTP Cookie File\n')
        f.write('# This is a generated file! Do not edit.\n\n')

        for cookie in cookies:
            # Format Netscape
            domain = cookie.get('domain', '')
            flag = 'TRUE'
            path = cookie.get('path', '/')
            secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
            expiration = str(int(cookie.get('expires', -1)))
            name = cookie.get('name', '')
            value = cookie.get('value', '')

            line = f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n"
            f.write(line)

    print(f"✅ {len(cookies)} cookies sauvegardés dans {output_file}")


def keep_cookie_alive(cookie_file: str = None, headless: bool = True, duration: int = 30):
    """
    Maintient le cookie en vie en visitant YouTube

    Args:
        cookie_file: Chemin vers le fichier cookie (défaut: COOKIE_FILE)
        headless: Mode headless (défaut: True)
        duration: Durée de la visite en secondes (défaut: 30)

    Returns:
        bool: True si succès, False sinon
    """
    if cookie_file is None:
        cookie_file = str(COOKIE_FILE)

    print("\n" + "=" * 70)
    print(f"🍪 COOKIE KEEPER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"📂 Cookie file: {cookie_file}")
    print(f"🎭 Headless: {headless}")
    print(f"⏱️  Durée visite: {duration}s")
    print("")

    # Vérifier que le fichier existe
    if not os.path.exists(cookie_file):
        print(f"❌ ERREUR: Fichier cookie introuvable: {cookie_file}")
        return False

    try:
        with sync_playwright() as p:
            print("🚀 [STEP 1] Lancement du navigateur...")

            # Lancer Chromium
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )

            print("✅ Navigateur lancé")

            # Créer un contexte
            print("🌐 [STEP 2] Création du contexte navigateur...")
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='fr-FR',
            )

            # Charger les cookies
            print("🍪 [STEP 3] Chargement des cookies...")
            cookies = parse_netscape_cookies(cookie_file)

            if not cookies:
                print("❌ ERREUR: Aucun cookie chargé")
                browser.close()
                return False

            context.add_cookies(cookies)
            print(f"✅ {len(cookies)} cookies injectés")

            # Créer une page
            print("📄 [STEP 4] Création de la page...")
            page = context.new_page()

            # Visiter YouTube
            print("🎬 [STEP 5] Visite de YouTube...")
            page.goto('https://www.youtube.com', wait_until='domcontentloaded', timeout=30000)
            print("✅ Page YouTube chargée")

            # Attendre un peu pour que tout se charge
            wait_time = random.randint(2, 4)
            print(f"⏳ Attente {wait_time}s pour chargement complet...")
            time.sleep(wait_time)

            # Scroller comme un humain
            print("📜 [STEP 6] Simulation activité humaine (scroll)...")
            scroll_count = random.randint(2, 4)
            for i in range(scroll_count):
                scroll_amount = random.randint(300, 800)
                page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                print(f"   Scroll {i+1}/{scroll_count} : {scroll_amount}px")

                # Pause aléatoire entre scrolls
                pause = random.uniform(1.5, 3.5)
                time.sleep(pause)

            # Rester un peu sur la page
            remaining = duration - (scroll_count * 2.5) - wait_time
            if remaining > 0:
                print(f"⏳ Repos sur la page : {remaining:.1f}s...")
                time.sleep(remaining)

            # Récupérer les cookies mis à jour
            print("💾 [STEP 7] Récupération des cookies mis à jour...")
            updated_cookies = context.cookies()
            print(f"✅ {len(updated_cookies)} cookies récupérés")

            # Sauvegarder les cookies
            print("💾 [STEP 8] Sauvegarde des cookies...")
            save_cookies_to_netscape(updated_cookies, cookie_file)

            # Fermer proprement
            print("🔒 [STEP 9] Fermeture du navigateur...")
            page.close()
            context.close()
            browser.close()

            print("")
            print("=" * 70)
            print("✅ COOKIE KEEPER : SUCCÈS")
            print("=" * 70)
            print(f"⏰ Durée totale : {duration}s")
            print(f"📅 Prochain refresh recommandé : dans 2-3 heures")
            print("")

            # Mettre à jour le statut
            from cookie_monitor import CookieStatus
            monitor = CookieStatus()
            monitor.update_status('ok', 'Cookie rafraîchi avec succès par le keeper', is_success=True)

            return True

    except Exception as e:
        print("")
        print("=" * 70)
        print("❌ COOKIE KEEPER : ÉCHEC")
        print("=" * 70)
        print(f"Erreur : {str(e)}")
        print("")

        # Mettre à jour le statut
        try:
            from cookie_monitor import CookieStatus
            monitor = CookieStatus()
            monitor.update_status('warning', f'Cookie keeper échoué : {str(e)}', is_success=False)
        except:
            pass

        return False


if __name__ == "__main__":
    # Test du cookie keeper
    import argparse

    parser = argparse.ArgumentParser(description='Cookie Keeper - Maintien en vie des cookies YouTube')
    parser.add_argument('--cookie-file', type=str, default=str(COOKIE_FILE), help='Chemin vers le fichier cookie')
    parser.add_argument('--headless', action='store_true', help='Mode headless (sans interface)')
    parser.add_argument('--duration', type=int, default=30, help='Durée de la visite (secondes)')

    args = parser.parse_args()

    success = keep_cookie_alive(
        cookie_file=args.cookie_file,
        headless=args.headless,
        duration=args.duration
    )

    exit(0 if success else 1)
