"""
Module d'upload automatique YouTube
Architecture scalable pour 1 à 10 comptes
"""

from .youtube_auth import YouTubeAuthenticator
from .youtube_uploader import YouTubeUploader
from .metadata_generator import MetadataGenerator
from .accounts_config import (
    YOUTUBE_ACCOUNTS,
    get_active_accounts,
    get_accounts_by_language,
    get_account_config
)

__all__ = [
    'YouTubeAuthenticator',
    'YouTubeUploader',
    'MetadataGenerator',
    'YOUTUBE_ACCOUNTS',
    'get_active_accounts',
    'get_accounts_by_language',
    'get_account_config',
]
