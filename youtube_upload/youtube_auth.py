#!/usr/bin/env python3
"""
Authentification OAuth 2.0 pour YouTube Data API v3
Gestion des credentials pour upload de vidéos
"""

import os
import sys
import pickle
import warnings
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Pour désactiver la vérification SSL si nécessaire (proxy d'entreprise)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Scopes nécessaires pour gérer le compte YouTube
# youtube.upload: Upload de vidéos
# youtube.force-ssl: Gestion des playlists, infos canal, etc.
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]


class YouTubeAuthenticator:
    """Gère l'authentification OAuth 2.0 pour YouTube"""

    def __init__(self, client_secrets_file='client_secrets.json', disable_ssl_verify=False):
        """
        Initialise l'authenticateur

        Args:
            client_secrets_file: Chemin vers le fichier OAuth client secrets
            disable_ssl_verify: Désactive la vérification SSL (pour proxy d'entreprise)
        """
        # Trouver la racine du projet (dossier parent de youtube_upload)
        current_dir = Path(__file__).parent
        project_root = current_dir.parent

        # Chercher client_secrets.json à la racine du projet
        self.client_secrets_file = project_root / client_secrets_file

        # Credentials dans youtube_upload/credentials/
        self.credentials_dir = current_dir / 'credentials'
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # Option pour désactiver SSL (proxy d'entreprise)
        self.disable_ssl_verify = disable_ssl_verify
        if self.disable_ssl_verify:
            print("⚠️  Vérification SSL désactivée (mode proxy d'entreprise)")

    def get_authenticated_service(self, account_id):
        """
        Obtient un service YouTube authentifié pour un compte

        Args:
            account_id: Identifiant du compte (ex: 'compte_test_1')

        Returns:
            Service YouTube API authentifié
        """
        # Vérifier que client_secrets.json existe
        if not self.client_secrets_file.exists():
            print(f"\n❌ ERREUR: Fichier client_secrets.json introuvable !")
            print(f"📍 Cherché dans: {self.client_secrets_file}")
            print("\n💡 Instructions:")
            print("1. Téléchargez le fichier OAuth depuis Google Cloud Console")
            print("2. Renommez-le en 'client_secrets.json'")
            print("3. Placez-le à la RACINE du projet:")
            print(f"   {self.client_secrets_file.parent}/")
            raise FileNotFoundError(f"client_secrets.json non trouvé dans {self.client_secrets_file.parent}")

        credentials_file = self.credentials_dir / f'{account_id}.json'
        credentials = None

        # Charger les credentials existants
        if credentials_file.exists():
            with open(credentials_file, 'rb') as f:
                credentials = pickle.load(f)

        # Si pas de credentials ou expirés, authentifier
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print(f"🔄 Rafraîchissement du token pour {account_id}...")
                credentials.refresh(Request())
            else:
                print(f"\n{'='*70}")
                print(f"🔐 AUTHENTIFICATION REQUISE POUR: {account_id}")
                print(f"{'='*70}")
                print("\n📋 Instructions:")
                print("1. Une fenêtre de navigateur va s'ouvrir")
                print("2. Connectez-vous avec le compte YouTube souhaité")
                print("3. Autorisez l'application à uploader des vidéos")
                print("4. Fermez la fenêtre une fois terminé")
                print(f"\n{'='*70}\n")

                input("Appuyez sur Entrée pour continuer...")

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file,
                    SCOPES
                )

                # Désactiver SSL si nécessaire (proxy d'entreprise)
                if self.disable_ssl_verify:
                    # Patcher la session OAuth pour désactiver SSL
                    original_request = flow.oauth2session.request

                    def patched_request(*args, **kwargs):
                        kwargs['verify'] = False
                        return original_request(*args, **kwargs)

                    flow.oauth2session.request = patched_request

                credentials = flow.run_local_server(
                    port=0,
                    prompt='consent',
                    authorization_prompt_message='Autorisation en cours...'
                )

            # Sauvegarder les credentials
            with open(credentials_file, 'wb') as f:
                pickle.dump(credentials, f)

            print(f"✅ Authentification réussie pour {account_id}")
            print(f"💾 Credentials sauvegardés: {credentials_file}\n")

        return build('youtube', 'v3', credentials=credentials)

    def authenticate_account(self, account_id):
        """
        Authentifie un compte spécifique (à lancer une fois par compte)

        Args:
            account_id: Identifiant du compte à authentifier
        """
        print(f"\n🚀 Authentification du compte: {account_id}")
        service = self.get_authenticated_service(account_id)

        # Tester la connexion
        try:
            channel = service.channels().list(
                part='snippet',
                mine=True
            ).execute()

            if channel.get('items'):
                channel_name = channel['items'][0]['snippet']['title']
                print(f"✅ Connexion réussie au compte: {channel_name}")
                return True
            else:
                print(f"⚠️  Aucune chaîne trouvée pour ce compte")
                return False

        except Exception as e:
            print(f"❌ Erreur lors du test de connexion: {e}")
            return False

    def list_authenticated_accounts(self):
        """Liste tous les comptes déjà authentifiés"""
        credentials_files = list(self.credentials_dir.glob('*.json'))

        if not credentials_files:
            print("📭 Aucun compte authentifié pour l'instant")
            return []

        print(f"\n📋 Comptes authentifiés ({len(credentials_files)}):")
        print("="*70)

        authenticated = []
        for cred_file in credentials_files:
            account_id = cred_file.stem
            print(f"  ✅ {account_id}")
            authenticated.append(account_id)

        print("="*70 + "\n")
        return authenticated


def main():
    """Script pour authentifier les comptes manuellement"""
    import argparse

    parser = argparse.ArgumentParser(description='Authentification YouTube OAuth 2.0')
    parser.add_argument('--account', type=str, help='ID du compte à authentifier')
    parser.add_argument('--list', action='store_true', help='Lister les comptes authentifiés')
    parser.add_argument('--no-ssl-verify', action='store_true',
                        help='Désactiver la vérification SSL (proxy d\'entreprise)')

    args = parser.parse_args()

    auth = YouTubeAuthenticator(disable_ssl_verify=args.no_ssl_verify)

    if args.list:
        auth.list_authenticated_accounts()
    elif args.account:
        auth.authenticate_account(args.account)
    else:
        print("Usage:")
        print("  python youtube_auth.py --account compte_test_1")
        print("  python youtube_auth.py --account compte_test_1 --no-ssl-verify")
        print("  python youtube_auth.py --list")


if __name__ == '__main__':
    main()
