#!/usr/bin/env python3
"""
Interactive Cookie Capture for YouTube
Opens a browser window for user to login, then captures cookies
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

class InteractiveCookieCapture:
    """Capture YouTube cookies interactively via user's browser login"""

    def __init__(self, cookies_dir: str = "/home/shorts/cookie_pool/cookies"):
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(parents=True, exist_ok=True)

    async def capture_cookies(self, account_name: str = "user") -> str:
        """
        Opens a browser for user to login to YouTube and captures cookies

        Args:
            account_name: Name to save the cookies under

        Returns:
            Path to the saved cookies file
        """
        print("\n" + "="*70)
        print("🌐 CAPTURE INTERACTIVE DE COOKIES YOUTUBE")
        print("="*70)
        print("\n📋 Instructions:")
        print("  1. Une fenêtre de navigateur va s'ouvrir")
        print("  2. Connectez-vous à votre compte YouTube")
        print("  3. Une fois connecté, les cookies seront capturés automatiquement")
        print("  4. Le navigateur se fermera automatiquement")
        print("\n⏳ Ouverture du navigateur...")

        async with async_playwright() as p:
            # Launch browser in visible mode (headless=False)
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )

            # Create context with realistic user agent
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 720}
            )

            page = await context.new_page()

            try:
                # Navigate to YouTube
                print("📍 Navigation vers YouTube...")
                await page.goto('https://www.youtube.com', wait_until='networkidle')

                print("\n✅ Navigateur ouvert!")
                print("👤 Veuillez vous connecter à votre compte YouTube...")
                print("   (Le script attend que vous soyez connecté...)\n")

                # Wait for user to login by checking for auth cookies
                await self._wait_for_login(page)

                print("\n✅ Connexion détectée!")
                print("📥 Extraction des cookies...")

                # Get all cookies
                cookies = await context.cookies()

                # Save cookies in Netscape format (compatible with yt-dlp)
                cookies_file = self.cookies_dir / f"{account_name}_cookies.txt"
                self._save_cookies_netscape(cookies, cookies_file)

                print(f"✅ Cookies sauvegardés: {cookies_file}")
                print(f"📊 Nombre de cookies: {len(cookies)}")

                # Also save in JSON format for reference
                json_file = self.cookies_dir / f"{account_name}_cookies.json"
                self._save_cookies_json(cookies, json_file)

                print("\n" + "="*70)
                print("✨ CAPTURE TERMINÉE AVEC SUCCÈS!")
                print("="*70)

                return str(cookies_file)

            finally:
                # Close browser
                await browser.close()

    async def _wait_for_login(self, page, timeout: int = 300000):
        """
        Wait for user to login by checking for YouTube auth cookies

        Args:
            page: Playwright page object
            timeout: Maximum wait time in milliseconds (default: 5 minutes)
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check if timeout exceeded
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            if elapsed > timeout:
                raise TimeoutError("Timeout waiting for login")

            # Get current cookies
            cookies = await page.context.cookies()

            # Check for YouTube authentication cookies
            # Key cookies that indicate logged-in state:
            # - LOGIN_INFO: present when logged in
            # - SAPISID, APISID: YouTube API session cookies
            # - SSID, SID: Google session cookies
            auth_cookies = [c['name'] for c in cookies if c['name'] in ['LOGIN_INFO', 'SAPISID', 'APISID', 'SSID', 'SID']]

            if len(auth_cookies) >= 3:  # Need at least 3 auth cookies to be confident
                return True

            # Wait a bit before checking again
            await asyncio.sleep(2)

    def _save_cookies_netscape(self, cookies: list, filepath: Path):
        """Save cookies in Netscape format (compatible with yt-dlp and curl)"""
        with open(filepath, 'w') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# This file was generated by interactive_cookie_capture.py\n")
            f.write("# Edit at your own risk.\n\n")

            for cookie in cookies:
                # Netscape format:
                # domain, flag, path, secure, expiration, name, value
                domain = cookie.get('domain', '')
                flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                path = cookie.get('path', '/')
                secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                expiration = str(int(cookie.get('expires', -1)))
                name = cookie.get('name', '')
                value = cookie.get('value', '')

                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n")

        # Set restrictive permissions
        os.chmod(filepath, 0o600)

    def _save_cookies_json(self, cookies: list, filepath: Path):
        """Save cookies in JSON format for reference"""
        cookies_data = {
            'captured_at': datetime.now().isoformat(),
            'cookies': cookies
        }

        with open(filepath, 'w') as f:
            json.dump(cookies_data, f, indent=2)

        # Set restrictive permissions
        os.chmod(filepath, 0o600)


async def main():
    """CLI entry point for interactive cookie capture"""
    import sys

    account_name = sys.argv[1] if len(sys.argv) > 1 else "user"

    capturer = InteractiveCookieCapture()
    cookies_path = await capturer.capture_cookies(account_name)

    print(f"\n📁 Cookies path: {cookies_path}")
    print("\n💡 Vous pouvez maintenant utiliser ce fichier de cookies avec yt-dlp")
    print(f"   Exemple: yt-dlp --cookies {cookies_path} <URL>\n")


if __name__ == "__main__":
    asyncio.run(main())
