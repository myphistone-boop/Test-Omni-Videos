#!/usr/bin/env python3
"""
Configuration des comptes YouTube (scalable pour 10 comptes)
Structure modulaire pour faciliter l'ajout de comptes
"""

# Configuration des comptes YouTube
# Pour l'instant : 1 compte de test
# Plus tard : étendre à 10 comptes

YOUTUBE_ACCOUNTS = {
    'compte_test_1': {
        'name': 'Compte Test 1',
        'language': 'fr',  # 'fr' ou 'en'
        'credentials_file': 'credentials/compte_test_1.json',
        'upload_time_range': (18, 20),  # Heure optimale de publication (18h-20h)
        'enabled': True,  # Permet d'activer/désactiver un compte
    },

    # Template pour ajouter d'autres comptes facilement
    # 'compte_fr_2': {
    #     'name': 'Viral FR 2',
    #     'language': 'fr',
    #     'credentials_file': 'credentials/compte_fr_2.json',
    #     'upload_time_range': (12, 13),
    #     'enabled': False,  # Désactivé pour l'instant
    # },
    # 'compte_en_1': {
    #     'name': 'Viral EN 1',
    #     'language': 'en',
    #     'credentials_file': 'credentials/compte_en_1.json',
    #     'upload_time_range': (17, 19),
    #     'enabled': False,
    # },
}


def get_active_accounts():
    """Retourne uniquement les comptes actifs"""
    return {k: v for k, v in YOUTUBE_ACCOUNTS.items() if v['enabled']}


def get_accounts_by_language(language):
    """Retourne les comptes d'une langue spécifique"""
    active = get_active_accounts()
    return {k: v for k, v in active.items() if v['language'] == language}


def get_account_config(account_id):
    """Récupère la config d'un compte spécifique"""
    return YOUTUBE_ACCOUNTS.get(account_id)
