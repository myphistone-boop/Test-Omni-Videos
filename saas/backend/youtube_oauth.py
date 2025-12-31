"""
OAuth YouTube authentication pour le SaaS
Gère la connexion Google et l'extraction des credentials YouTube
"""

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import json
from pathlib import Path

# Configuration OAuth
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

CLIENT_SECRETS_FILE = os.getenv('GOOGLE_CLIENT_SECRETS', 'client_secrets.json')
REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://184.174.36.43/api/auth/callback')


class YouTubeOAuth:
    """Gestionnaire OAuth pour YouTube"""

    def __init__(self):
        self.client_secrets_path = Path(__file__).parent.parent.parent / CLIENT_SECRETS_FILE

    def get_authorization_url(self, state: str) -> str:
        """
        Génère l'URL d'autorisation OAuth

        Args:
            state: Token CSRF pour sécuriser le flow

        Returns:
            URL d'autorisation Google
        """

        flow = Flow.from_client_secrets_file(
            str(self.client_secrets_path),
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

        flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )

        authorization_url, state = flow.authorization_url()
        return authorization_url

    def exchange_code_for_token(self, code: str, state: str) -> dict:
        """
        Échange le code d'autorisation contre un token

        Args:
            code: Code d'autorisation reçu de Google
            state: Token CSRF pour validation

        Returns:
            Dict contenant les credentials et infos utilisateur
        """

        flow = Flow.from_client_secrets_file(
            str(self.client_secrets_path),
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            state=state
        )

        flow.fetch_token(code=code)

        credentials = flow.credentials

        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

    def refresh_token(self, refresh_token: str) -> str:
        """
        Rafraîchit un access token expiré

        Args:
            refresh_token: Refresh token Google

        Returns:
            Nouveau access token
        """

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
        )

        credentials.refresh(Request())
        return credentials.token
