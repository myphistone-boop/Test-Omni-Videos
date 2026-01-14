"""
Cookie Refresher - Auto-refresh des cookies YouTube via Playwright
Connexion automatique + extraction cookies + sauvegarde
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime


class CookieRefresher:
    """Rafraîchit automatiquement les cookies YouTube"""

    def __init__(self, cookies_dir: str = "/home/shorts/cookie_pool"):
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(parents=True, exist_ok=True)

        # Fichier de configuration des comptes
        self.config_file = self.cookies_dir / "accounts_config.json"

    def load_accounts_config(self) -> List[Dict]:
        """
        Charge la configuration des comptes YouTube

        Format attendu (accounts_config.json):
        [
            {
                "account_id": "cookies_1",
                "email": "your-email@gmail.com",
                "password": "your-password"
            },
            {
                "account_id": "cookies_2",
                "email": "another@gmail.com",
                "password": "another-password"
            }
        ]

        Returns:
            List[Dict]: Liste des comptes configurés
        """

        if not self.config_file.exists():
            print(f"⚠️  Fichier de configuration introuvable: {self.config_file}")
            print("   Créez-le avec le format ci-dessus")
            return []

        try:
            with open(self.config_file, 'r') as f:
                accounts = json.load(f)
                print(f"✅ {len(accounts)} compte(s) chargé(s) depuis la config")
                return accounts
        except Exception as e:
            print(f"❌ Erreur lecture config: {e}")
            return []

    def refresh_account_cookies(self, account: Dict, headless: bool = True) -> bool:
        """
        Rafraîchit les cookies d'un compte YouTube

        Args:
            account: Dict avec keys: account_id, email, password
            headless: Mode headless (True en production)

        Returns:
            bool: True si succès, False sinon
        """

        try:
            from playwright.sync_api import sync_playwright

            account_id = account['account_id']
            email = account['email']
            password = account['password']

            print(f"\n{'='*60}")
            print(f"🔄 Rafraîchissement des cookies: {account_id}")
            print(f"{'='*60}")

            with sync_playwright() as p:
                # Lancer le navigateur
                print("   [1/6] Lancement du navigateur...")
                browser = p.chromium.launch(headless=headless)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()

                # Aller sur YouTube
                print("   [2/6] Navigation vers YouTube...")
                page.goto('https://www.youtube.com', wait_until='networkidle', timeout=30000)
                time.sleep(2)

                # Cliquer sur "Sign in"
                print("   [3/6] Clic sur Sign In...")
                try:
                    # Essayer plusieurs sélecteurs possibles
                    sign_in_selectors = [
                        'a[aria-label*="Sign in"]',
                        'a:has-text("Sign in")',
                        'ytd-button-renderer a:has-text("Sign in")'
                    ]

                    clicked = False
                    for selector in sign_in_selectors:
                        try:
                            page.click(selector, timeout=5000)
                            clicked = True
                            break
                        except:
                            continue

                    if not clicked:
                        print("      ⚠️  Bouton Sign In non trouvé, tentative URL directe...")
                        page.goto('https://accounts.google.com/ServiceLogin?service=youtube', wait_until='networkidle')

                except Exception as e:
                    print(f"      ⚠️  Erreur clic Sign In: {e}, tentative URL directe...")
                    page.goto('https://accounts.google.com/ServiceLogin?service=youtube', wait_until='networkidle')

                time.sleep(3)

                # Entrer l'email
                print(f"   [4/6] Saisie de l'email: {email[:3]}***@{email.split('@')[1]}")
                page.fill('input[type="email"]', email)
                page.click('button:has-text("Next"), #identifierNext')
                time.sleep(3)

                # Entrer le mot de passe
                print("   [5/6] Saisie du mot de passe...")
                page.fill('input[type="password"]', password)
                page.click('button:has-text("Next"), #passwordNext')

                # Attendre la redirection vers YouTube
                print("   [6/6] Attente de la connexion...")
                try:
                    page.wait_for_url('*://www.youtube.com/*', timeout=30000)
                    print("      ✅ Connecté à YouTube !")
                except:
                    print("      ⚠️  URL pas encore youtube.com, attente supplémentaire...")
                    time.sleep(5)

                    # Vérifier si on est bien connecté
                    current_url = page.url
                    if 'youtube.com' not in current_url:
                        print(f"      ❌ ÉCHEC: Toujours sur {current_url}")
                        print("      Possible problème: 2FA, CAPTCHA, ou mauvais credentials")
                        browser.close()
                        return False

                # Attendre que la page soit complètement chargée
                time.sleep(5)

                # Extraire les cookies
                print("   [7/6] Extraction des cookies...")
                cookies = context.cookies()

                # Convertir au format Netscape (compatible yt-dlp)
                cookies_path = self.cookies_dir / f"{account_id}.txt"
                self._save_cookies_netscape(cookies, cookies_path)

                print(f"   ✅ {len(cookies)} cookies sauvegardés: {cookies_path}")

                # Nettoyer
                browser.close()

                print(f"✅ Succès pour {account_id}")
                return True

        except ImportError:
            print("❌ Playwright non installé!")
            print("   Installez avec: pip install playwright && playwright install chromium")
            return False
        except Exception as e:
            print(f"❌ Erreur lors du refresh: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _save_cookies_netscape(self, cookies: List[Dict], output_path: Path):
        """
        Sauvegarde les cookies au format Netscape (compatible yt-dlp)

        Args:
            cookies: Liste des cookies Playwright
            output_path: Chemin de sortie
        """

        with open(output_path, 'w') as f:
            # Header Netscape
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# This file is generated by Cookie Refresher. Do not edit.\n\n")

            for cookie in cookies:
                # Format Netscape: domain, flag, path, secure, expiration, name, value
                domain = cookie.get('domain', '')
                flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                path = cookie.get('path', '/')
                secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                expiration = str(int(cookie.get('expires', -1)))
                name = cookie.get('name', '')
                value = cookie.get('value', '')

                # Écrire la ligne
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n")

        # Permissions 600 (sécurité)
        output_path.chmod(0o600)

    def refresh_all_accounts(self, headless: bool = True) -> Dict[str, bool]:
        """
        Rafraîchit tous les comptes du pool

        Args:
            headless: Mode headless

        Returns:
            Dict[account_id, success]: Résultats par compte
        """

        print("\n" + "="*60)
        print("🔄 RAFRAÎCHISSEMENT DE TOUS LES COMPTES")
        print("="*60)

        accounts = self.load_accounts_config()

        if not accounts:
            print("❌ Aucun compte configuré")
            return {}

        results = {}

        for i, account in enumerate(accounts, 1):
            print(f"\n[{i}/{len(accounts)}] Traitement de {account['account_id']}...")

            success = self.refresh_account_cookies(account, headless=headless)
            results[account['account_id']] = success

            # Délai entre comptes pour éviter détection
            if i < len(accounts):
                print("   ⏳ Pause 10s avant le compte suivant...")
                time.sleep(10)

        # Résumé
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DU RAFRAÎCHISSEMENT")
        print("="*60)

        success_count = sum(1 for v in results.values() if v)
        failure_count = len(results) - success_count

        for account_id, success in results.items():
            status = "✅ Succès" if success else "❌ Échec"
            print(f"   {status}: {account_id}")

        print(f"\n   Total: {success_count}/{len(results)} comptes rafraîchis")
        print("="*60 + "\n")

        return results

    def create_sample_config(self):
        """Crée un fichier de configuration exemple"""

        sample_config = [
            {
                "account_id": "cookies_1",
                "email": "your-email-1@gmail.com",
                "password": "your-password-1",
                "notes": "Compte principal"
            },
            {
                "account_id": "cookies_2",
                "email": "your-email-2@gmail.com",
                "password": "your-password-2",
                "notes": "Compte secondaire"
            },
            {
                "account_id": "cookies_3",
                "email": "your-email-3@gmail.com",
                "password": "your-password-3",
                "notes": "Compte tertiaire"
            }
        ]

        sample_path = self.cookies_dir / "accounts_config.json.example"

        with open(sample_path, 'w') as f:
            json.dump(sample_config, f, indent=2)

        print(f"✅ Fichier exemple créé: {sample_path}")
        print("   Copiez-le en accounts_config.json et modifiez avec vos identifiants")


def main():
    """Fonction principale pour test/cron"""

    import argparse

    parser = argparse.ArgumentParser(description="Rafraîchir les cookies YouTube")
    parser.add_argument('--cookies-dir', default='/home/shorts/cookie_pool',
                        help='Répertoire des cookies')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Mode headless (défaut: True)')
    parser.add_argument('--visible', action='store_true',
                        help='Mode visible (debug)')
    parser.add_argument('--create-config', action='store_true',
                        help='Créer un fichier de config exemple')

    args = parser.parse_args()

    refresher = CookieRefresher(cookies_dir=args.cookies_dir)

    if args.create_config:
        refresher.create_sample_config()
        return

    headless = not args.visible

    # Rafraîchir tous les comptes
    results = refresher.refresh_all_accounts(headless=headless)

    # Exit code basé sur le succès
    if all(results.values()):
        print("✅ Tous les comptes rafraîchis avec succès")
        exit(0)
    else:
        print("⚠️  Certains comptes ont échoué")
        exit(1)


if __name__ == "__main__":
    main()
