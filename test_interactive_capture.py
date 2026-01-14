#!/usr/bin/env python3
"""
Script de test pour la capture interactive de cookies YouTube
"""

import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'saas', 'backend'))

from interactive_cookie_capture import InteractiveCookieCapture
import asyncio

async def test_capture():
    """Test la capture interactive de cookies"""

    print("\n" + "="*70)
    print("🧪 TEST: Capture Interactive de Cookies YouTube")
    print("="*70)
    print()

    # Créer le capturer
    capturer = InteractiveCookieCapture(
        cookies_dir="/home/user/Test-Omni-Videos/test_cookies"
    )

    # Lancer la capture
    try:
        cookies_path = await capturer.capture_cookies(account_name="test_user")

        print("\n" + "="*70)
        print("✅ TEST RÉUSSI!")
        print("="*70)
        print(f"\n📁 Cookies sauvegardés: {cookies_path}")

        # Vérifier que le fichier existe et contient des données
        if os.path.exists(cookies_path):
            file_size = os.path.getsize(cookies_path)
            print(f"📊 Taille du fichier: {file_size} octets")

            # Afficher les premières lignes
            print("\n📄 Aperçu du fichier cookies:")
            print("-" * 70)
            with open(cookies_path, 'r') as f:
                lines = f.readlines()[:10]
                for line in lines:
                    print(f"   {line.rstrip()}")
            print("-" * 70)

            print("\n✅ Le fichier de cookies est valide!")
        else:
            print("\n❌ ERREUR: Le fichier de cookies n'existe pas!")

    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST ÉCHOUÉ!")
        print("="*70)
        print(f"\nErreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_capture())
