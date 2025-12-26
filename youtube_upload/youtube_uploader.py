#!/usr/bin/env python3
"""
Module d'upload de vidéos sur YouTube
Gère l'upload automatique avec métadonnées générées
"""

import os
import sys
import time
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from youtube_auth import YouTubeAuthenticator
from metadata_generator import MetadataGenerator
from accounts_config import get_account_config


class YouTubeUploader:
    """Gère l'upload de vidéos sur YouTube"""

    def __init__(self):
        """Initialise l'uploader"""
        self.authenticator = YouTubeAuthenticator()
        self.metadata_generator = MetadataGenerator()

    def upload_video(self, video_path, original_title, account_id, custom_metadata=None):
        """
        Upload une vidéo sur YouTube

        Args:
            video_path: Chemin vers la vidéo à uploader
            original_title: Titre original de la vidéo source
            account_id: ID du compte YouTube à utiliser
            custom_metadata: Métadonnées personnalisées optionnelles

        Returns:
            Dict avec les infos de la vidéo uploadée ou None en cas d'erreur
        """
        # Vérifier que le fichier existe
        if not os.path.exists(video_path):
            print(f"❌ Fichier introuvable: {video_path}")
            return None

        # Récupérer la config du compte
        account_config = get_account_config(account_id)
        if not account_config:
            print(f"❌ Compte inconnu: {account_id}")
            return None

        # Générer les métadonnées
        language = account_config['language']
        if custom_metadata:
            metadata = custom_metadata
        else:
            metadata = self.metadata_generator.generate_all_metadata(
                original_title,
                language
            )

        print(f"\n{'='*70}")
        print(f"📤 UPLOAD VERS YOUTUBE")
        print(f"{'='*70}")
        print(f"📺 Compte: {account_config['name']}")
        print(f"📁 Fichier: {Path(video_path).name}")
        print(f"✏️  Titre: {metadata['title']}")
        print(f"🌍 Langue: {language.upper()}")
        print(f"{'='*70}\n")

        try:
            # Authentification
            print("🔐 Authentification...")
            youtube = self.authenticator.get_authenticated_service(account_id)

            # Préparer les métadonnées pour l'API
            body = {
                'snippet': {
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'tags': metadata['tags'],
                    'categoryId': metadata.get('category', '22'),
                },
                'status': {
                    'privacyStatus': metadata.get('privacy_status', 'public'),
                    'selfDeclaredMadeForKids': False,
                }
            }

            # Préparer le fichier
            print("📦 Préparation du fichier...")
            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024,  # 1MB chunks
                resumable=True
            )

            # Lancer l'upload
            print("⏳ Upload en cours...")
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            last_progress = 0

            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress > last_progress:
                        print(f"   {progress}% uploadé...")
                        last_progress = progress

            # Succès !
            video_id = response['id']
            video_url = f"https://youtube.com/shorts/{video_id}"

            print(f"\n{'='*70}")
            print(f"✅ UPLOAD RÉUSSI !")
            print(f"{'='*70}")
            print(f"🆔 Video ID: {video_id}")
            print(f"🔗 URL: {video_url}")
            print(f"✏️  Titre: {metadata['title']}")
            print(f"{'='*70}\n")

            return {
                'video_id': video_id,
                'url': video_url,
                'title': metadata['title'],
                'account': account_id,
                'upload_time': time.time(),
            }

        except HttpError as e:
            print(f"\n❌ Erreur API YouTube: {e}")

            # Gérer les quotas dépassés
            if e.resp.status == 403:
                print("⚠️  Quota API probablement dépassé")
                print("💡 Attendez demain ou utilisez un autre projet Google Cloud")

            return None

        except Exception as e:
            print(f"\n❌ Erreur inattendue: {e}")
            import traceback
            traceback.print_exc()
            return None

    def upload_multiple_videos(self, videos_data, delay_between_uploads=60):
        """
        Upload plusieurs vidéos avec délai entre chaque

        Args:
            videos_data: Liste de dicts avec 'video_path', 'original_title', 'account_id'
            delay_between_uploads: Délai en secondes entre chaque upload

        Returns:
            Liste des résultats d'upload
        """
        results = []

        for i, video_data in enumerate(videos_data, 1):
            print(f"\n🎬 Upload {i}/{len(videos_data)}")

            result = self.upload_video(
                video_data['video_path'],
                video_data['original_title'],
                video_data['account_id'],
                video_data.get('custom_metadata')
            )

            results.append(result)

            # Délai entre uploads (sauf pour le dernier)
            if i < len(videos_data) and delay_between_uploads > 0:
                print(f"⏸️  Attente de {delay_between_uploads}s avant le prochain upload...")
                time.sleep(delay_between_uploads)

        # Résumé
        success_count = sum(1 for r in results if r is not None)
        fail_count = len(results) - success_count

        print(f"\n{'='*70}")
        print(f"📊 RÉSUMÉ DES UPLOADS")
        print(f"{'='*70}")
        print(f"✅ Succès: {success_count}/{len(results)}")
        print(f"❌ Échecs: {fail_count}/{len(results)}")
        print(f"{'='*70}\n")

        return results


def main():
    """Test de l'uploader"""
    import argparse

    parser = argparse.ArgumentParser(description='Upload vidéo sur YouTube')
    parser.add_argument('--video', type=str, help='Chemin vers la vidéo')
    parser.add_argument('--title', type=str, help='Titre original')
    parser.add_argument('--account', type=str, default='compte_test_1', help='ID du compte')

    args = parser.parse_args()

    if not args.video or not args.title:
        print("Usage: python youtube_uploader.py --video path/to/video.mp4 --title 'Original Title'")
        sys.exit(1)

    uploader = YouTubeUploader()
    uploader.upload_video(args.video, args.title, args.account)


if __name__ == '__main__':
    main()
