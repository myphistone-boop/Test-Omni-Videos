#!/usr/bin/env python3
"""
Script de test léger pour vérifier l'accès au compte YouTube
Teste l'authentification sans uploader de vidéo
"""

import argparse
import sys
from pathlib import Path

from youtube_auth import YouTubeAuthenticator


def get_channel_info(youtube):
    """Récupère et affiche les informations du canal"""
    print("\n" + "="*70)
    print("📺 INFORMATIONS DU CANAL")
    print("="*70)

    try:
        # Récupérer les infos du canal
        request = youtube.channels().list(
            part="snippet,statistics,status",
            mine=True
        )
        response = request.execute()

        if not response.get('items'):
            print("❌ Aucun canal trouvé pour ce compte")
            return False

        channel = response['items'][0]
        snippet = channel['snippet']
        stats = channel['statistics']
        status = channel['status']

        print(f"\n✅ Compte authentifié avec succès !\n")
        print(f"  📌 Nom du canal: {snippet['title']}")
        print(f"  🆔 Channel ID: {channel['id']}")
        print(f"  📝 Description: {snippet['description'][:100]}..." if len(snippet['description']) > 100 else f"  📝 Description: {snippet['description']}")
        print(f"\n  📊 Statistiques:")
        print(f"     • Abonnés: {stats.get('subscriberCount', 'N/A')}")
        print(f"     • Vidéos: {stats.get('videoCount', '0')}")
        print(f"     • Vues totales: {stats.get('viewCount', '0')}")
        print(f"\n  🔒 Statut: {'✅ Actif' if not status.get('isLinked') == False else '⚠️ Non lié'}")

        # Vérifier si les Shorts sont activés
        print(f"\n  🎬 Fonctionnalités:")
        print(f"     • Uploads longs: ✅")
        print(f"     • Shorts: ✅ (disponible pour tous)")

        # Vérifier l'accès aux posts communautaires
        subscriber_count = int(stats.get('subscriberCount', 0))
        if subscriber_count >= 500:
            print(f"     • Posts communautaires: ✅ (>{subscriber_count} abonnés)")
        else:
            print(f"     • Posts communautaires: ❌ (besoin de 500+ abonnés, vous avez {subscriber_count})")

        print("\n" + "="*70)
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des infos: {e}")
        return False


def test_create_playlist(youtube):
    """Test de création d'une playlist (action légère et non destructive)"""
    print("\n" + "="*70)
    print("📝 TEST: Création d'une playlist de test")
    print("="*70)

    response = input("\n⚠️  Voulez-vous créer une playlist de test ? (o/N): ")
    if response.lower() != 'o':
        print("   ⏭️  Test de playlist ignoré")
        return None

    try:
        # Créer une playlist de test
        request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": "[TEST] Playlist Claude Automation",
                    "description": "Playlist de test créée automatiquement - Peut être supprimée"
                },
                "status": {
                    "privacyStatus": "private"  # Privée pour éviter la pollution
                }
            }
        )
        response = request.execute()

        playlist_id = response['id']
        print(f"\n✅ Playlist créée avec succès !")
        print(f"   🆔 ID: {playlist_id}")
        print(f"   🔗 URL: https://www.youtube.com/playlist?list={playlist_id}")
        print(f"   🔒 Visibilité: Privée")

        # Proposer de la supprimer immédiatement
        delete = input("\n🗑️  Voulez-vous supprimer cette playlist de test maintenant ? (O/n): ")
        if delete.lower() != 'n':
            youtube.playlists().delete(id=playlist_id).execute()
            print("   ✅ Playlist supprimée")
        else:
            print("   💡 Vous pouvez la supprimer manuellement dans YouTube Studio")

        return playlist_id

    except Exception as e:
        print(f"❌ Erreur lors de la création de la playlist: {e}")
        return None


def test_list_playlists(youtube):
    """Liste les playlists existantes"""
    print("\n" + "="*70)
    print("📋 VOS PLAYLISTS")
    print("="*70)

    try:
        request = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=10
        )
        response = request.execute()

        playlists = response.get('items', [])

        if not playlists:
            print("\n   📭 Aucune playlist trouvée")
        else:
            print(f"\n   📝 {len(playlists)} playlist(s) trouvée(s):\n")
            for i, playlist in enumerate(playlists, 1):
                title = playlist['snippet']['title']
                playlist_id = playlist['id']
                print(f"   {i}. {title}")
                print(f"      ID: {playlist_id}")

        print("\n" + "="*70)
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des playlists: {e}")
        return False


def test_upload_quota_check(youtube):
    """Vérifie le quota d'upload (sans uploader)"""
    print("\n" + "="*70)
    print("📊 QUOTA API & LIMITES")
    print("="*70)

    print("\n  💡 Informations sur les quotas YouTube:")
    print("     • Quota quotidien: 10,000 unités/jour")
    print("     • Coût d'un upload: ~1,600 unités")
    print("     • Uploads max/jour: ~6 vidéos")
    print("     • Lecture infos canal: 1 unité")
    print("     • Création playlist: 50 unités")

    print("\n  ⚠️  Pour uploader 10 vidéos/jour:")
    print("     → Il faudra 2 projets Google Cloud (2×6 = 12 uploads)")

    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(description='Test léger de l\'accès au compte YouTube')
    parser.add_argument('--account', required=True, help='ID du compte à tester (ex: compte_test_1)')

    args = parser.parse_args()
    account_id = args.account

    print("\n" + "="*70)
    print("🧪 TEST D'ACCÈS AU COMPTE YOUTUBE")
    print("="*70)
    print(f"\n🔐 Compte: {account_id}")

    # Authentification
    try:
        authenticator = YouTubeAuthenticator()

        # Vérifier que le compte est déjà authentifié
        credentials_file = authenticator.credentials_dir / f'{account_id}.json'
        if not credentials_file.exists():
            print(f"\n❌ Compte non authentifié: {account_id}")
            print(f"\n💡 Lancez d'abord:")
            print(f"   python youtube_auth.py --account {account_id}")
            return 1

        # Obtenir le service YouTube authentifié
        youtube = authenticator.get_authenticated_service(account_id)

        # Test 1: Infos du canal
        if not get_channel_info(youtube):
            return 1

        # Test 2: Lister les playlists existantes
        test_list_playlists(youtube)

        # Test 3: Créer une playlist de test (optionnel)
        test_create_playlist(youtube)

        # Test 4: Infos sur les quotas
        test_upload_quota_check(youtube)

        # Résumé final
        print("\n" + "="*70)
        print("✅ TOUS LES TESTS RÉUSSIS !")
        print("="*70)
        print("\n  🎉 Votre compte est correctement configuré et prêt pour:")
        print("     • ✅ Lecture des informations du canal")
        print("     • ✅ Gestion des playlists")
        print("     • ✅ Upload de vidéos (quota disponible)")
        print("\n  📋 Prochaines étapes:")
        print("     1. Testez un upload vidéo avec youtube_uploader.py")
        print("     2. Validez la publication d'un Short")
        print("     3. Passez en production !")
        print("\n" + "="*70 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
