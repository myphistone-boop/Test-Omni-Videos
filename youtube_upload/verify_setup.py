#!/usr/bin/env python3
"""
Script de vérification de la configuration YouTube Upload
Vérifie que tous les prérequis sont en place avant l'authentification
"""

import sys
from pathlib import Path
import json

def check_client_secrets():
    """Vérifie la présence et validité de client_secrets.json"""
    project_root = Path(__file__).parent.parent
    client_secrets_path = project_root / 'client_secrets.json'

    print("🔍 Vérification de client_secrets.json...")

    if not client_secrets_path.exists():
        print(f"  ❌ Fichier NON TROUVÉ: {client_secrets_path}")
        print(f"\n  📍 Le fichier doit être placé à la racine du projet:")
        print(f"     {project_root}/")
        print(f"\n  💡 Téléchargez-le depuis Google Cloud Console:")
        print(f"     APIs & Services → Credentials → Download OAuth 2.0 Client")
        return False

    # Vérifier que c'est un JSON valide
    try:
        with open(client_secrets_path, 'r') as f:
            data = json.load(f)

        # Vérifier la structure
        if 'installed' not in data and 'web' not in data:
            print(f"  ⚠️  Format JSON invalide - manque 'installed' ou 'web'")
            return False

        client_type = 'installed' if 'installed' in data else 'web'
        client_id = data[client_type].get('client_id', 'N/A')

        print(f"  ✅ Fichier trouvé et valide")
        print(f"     Type: {client_type}")
        print(f"     Client ID: {client_id[:20]}...")
        return True

    except json.JSONDecodeError:
        print(f"  ❌ Fichier invalide - pas un JSON valide")
        return False
    except Exception as e:
        print(f"  ❌ Erreur lors de la lecture: {e}")
        return False


def check_dependencies():
    """Vérifie que les dépendances Python sont installées"""
    print("\n🔍 Vérification des dépendances Python...")

    import subprocess

    required_packages = [
        'google-auth',
        'google-auth-oauthlib',
        'google-api-python-client',
    ]

    all_ok = True
    for package_name in required_packages:
        try:
            result = subprocess.run(
                ['pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"  ✅ {package_name}")
            else:
                print(f"  ❌ {package_name} - NON INSTALLÉ")
                all_ok = False
        except Exception as e:
            print(f"  ⚠️  {package_name} - Impossible de vérifier")
            # Don't fail on check errors
            pass

    if not all_ok:
        print(f"\n  💡 Installez les dépendances manquantes:")
        print(f"     pip install -r requirements.txt")

    return all_ok


def check_accounts_config():
    """Vérifie la configuration des comptes"""
    print("\n🔍 Vérification de accounts_config.py...")

    try:
        from accounts_config import YOUTUBE_ACCOUNTS, get_active_accounts

        active = get_active_accounts()

        if not active:
            print(f"  ⚠️  Aucun compte actif configuré")
            return False

        print(f"  ✅ {len(active)} compte(s) actif(s):")
        for account_id in active:
            account = YOUTUBE_ACCOUNTS[account_id]
            print(f"     • {account_id} ({account['language'].upper()})")

        return True

    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False


def check_credentials_dir():
    """Vérifie le dossier credentials"""
    print("\n🔍 Vérification du dossier credentials/...")

    creds_dir = Path(__file__).parent / 'credentials'

    if not creds_dir.exists():
        print(f"  ⚠️  Dossier non trouvé (sera créé automatiquement)")
        return True

    creds_files = list(creds_dir.glob('*.json'))

    if not creds_files:
        print(f"  📭 Aucun compte authentifié pour l'instant")
        print(f"     (Normal si c'est la première utilisation)")
    else:
        print(f"  ✅ {len(creds_files)} compte(s) déjà authentifié(s):")
        for cred_file in creds_files:
            print(f"     • {cred_file.stem}")

    return True


def print_next_steps(all_checks_passed):
    """Affiche les prochaines étapes"""
    print("\n" + "="*70)

    if all_checks_passed:
        print("✅ CONFIGURATION COMPLÈTE - PRÊT POUR L'AUTHENTIFICATION !")
        print("="*70)
        print("\n📋 Prochaines étapes:")
        print("\n1️⃣  Ajouter votre email dans Google Cloud Console:")
        print("   → APIs & Services → OAuth consent screen → Test users → + ADD USERS")
        print("\n2️⃣  Lancer l'authentification:")
        print("   python youtube_auth.py --account compte_test_1")
        print("\n3️⃣  Tester un upload:")
        print("   python youtube_uploader.py --video VIDEO.mp4 --title \"Test\" --account compte_test_1")
    else:
        print("⚠️  CONFIGURATION INCOMPLÈTE - ACTION REQUISE")
        print("="*70)
        print("\n📋 Corrigez les erreurs ci-dessus avant de continuer.")
        print("\nConsultez SETUP_CHECKLIST.md pour les instructions détaillées.")

    print("="*70 + "\n")


def main():
    """Exécute toutes les vérifications"""
    print("\n" + "="*70)
    print("🔧 VÉRIFICATION DE LA CONFIGURATION - MODULE YOUTUBE UPLOAD")
    print("="*70 + "\n")

    checks = [
        check_client_secrets(),
        check_dependencies(),
        check_accounts_config(),
        check_credentials_dir(),
    ]

    all_ok = all(checks)
    print_next_steps(all_ok)

    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
