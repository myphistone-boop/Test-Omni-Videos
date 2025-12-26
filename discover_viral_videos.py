#!/usr/bin/env python3
"""
Module de découverte de vidéos virales YouTube
- Recherche les vidéos tendance de moins de 24h
- Filtre par durée (<15 min)
- Calcule un score de viralité
- Sélectionne top 5 FR + top 5 EN
"""

import os
import sys
import ssl
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate
from tqdm import tqdm
import json
import httplib2

# Charger les variables d'environnement
load_dotenv()

class ViralVideoDiscovery:
    def __init__(self, api_key=None):
        """Initialise le découvreur de vidéos virales"""
        self.api_key = api_key or os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("❌ YOUTUBE_API_KEY manquante dans .env")

        # Créer un client HTTP qui ignore les erreurs SSL (nécessaire pour certains proxies/antivirus)
        try:
            # Essayer d'abord avec vérification SSL
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        except ssl.SSLError:
            # Si erreur SSL, désactiver la vérification
            print("⚠️  Problème SSL détecté, désactivation de la vérification...")
            http = httplib2.Http()
            http.disable_ssl_certificate_validation = True
            self.youtube = build('youtube', 'v3', developerKey=self.api_key, http=http)

        self.max_duration_minutes = 15
        self.max_age_hours = 24

    def get_trending_videos(self, region_code='US', max_results=50):
        """Récupère les vidéos tendance pour une région"""
        print(f"\n🔍 Recherche des vidéos tendance ({region_code})...")

        try:
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=max_results,
                videoCategoryId='0'  # Toutes catégories
            )
            response = request.execute()
            return response.get('items', [])

        except ssl.SSLError as e:
            print(f"❌ Erreur SSL: {e}")
            print("💡 Tentative avec désactivation de la vérification SSL...")
            # Recréer le client avec SSL désactivé
            http = httplib2.Http()
            http.disable_ssl_certificate_validation = True
            self.youtube = build('youtube', 'v3', developerKey=self.api_key, http=http)
            # Réessayer la requête
            try:
                request = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    chart='mostPopular',
                    regionCode=region_code,
                    maxResults=max_results,
                    videoCategoryId='0'
                )
                response = request.execute()
                return response.get('items', [])
            except Exception as e:
                print(f"❌ Erreur après désactivation SSL: {e}")
                return []

        except HttpError as e:
            print(f"❌ Erreur API YouTube: {e}")
            return []

        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return []

    def filter_by_duration(self, videos):
        """Filtre les vidéos de moins de 15 minutes"""
        filtered = []

        for video in videos:
            duration_iso = video['contentDetails']['duration']
            duration = isodate.parse_duration(duration_iso)
            duration_minutes = duration.total_seconds() / 60

            if duration_minutes <= self.max_duration_minutes:
                video['duration_minutes'] = duration_minutes
                filtered.append(video)

        return filtered

    def filter_by_age(self, videos):
        """Filtre les vidéos de moins de 24h"""
        filtered = []
        now = datetime.now(datetime.timezone.utc)
        cutoff = now - timedelta(hours=self.max_age_hours)

        for video in videos:
            published_at = datetime.fromisoformat(
                video['snippet']['publishedAt'].replace('Z', '+00:00')
            )

            if published_at > cutoff:
                age_hours = (now - published_at).total_seconds() / 3600
                video['age_hours'] = age_hours
                filtered.append(video)

        return filtered

    def calculate_virality_score(self, video):
        """
        Calcule le score de viralité d'une vidéo

        Score = (Propagation * 0.5) + (Engagement * 0.4) + (Fraîcheur * 0.1)

        - Propagation : vues/heure (normalisé)
        - Engagement : (likes + comments) / vues (normalisé)
        - Fraîcheur : bonus pour vidéos très récentes (<12h)
        """
        stats = video.get('statistics', {})

        # Récupérer les métriques
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        age_hours = video.get('age_hours', 24)

        # Éviter division par zéro
        if age_hours == 0:
            age_hours = 0.1
        if views == 0:
            return 0

        # 1. Score de propagation (vues/heure)
        views_per_hour = views / age_hours
        propagation_score = min(views_per_hour / 10000, 100)  # Normalisé sur 100

        # 2. Score d'engagement
        engagement_rate = (likes + comments) / views
        engagement_score = min(engagement_rate * 1000, 100)  # Normalisé sur 100

        # 3. Score de fraîcheur
        freshness_score = 100 if age_hours < 12 else 50

        # Score final
        final_score = (
            propagation_score * 0.5 +
            engagement_score * 0.4 +
            freshness_score * 0.1
        )

        video['virality_score'] = round(final_score, 2)
        video['views_per_hour'] = round(views_per_hour, 2)
        video['engagement_rate'] = round(engagement_rate * 100, 2)  # En %

        return final_score

    def discover_viral_videos(self, language='fr', top_n=5):
        """
        Découvre les top N vidéos virales pour une langue

        Args:
            language: 'fr' ou 'en'
            top_n: nombre de vidéos à retourner

        Returns:
            Liste des top N vidéos triées par score de viralité
        """
        region_code = 'FR' if language == 'fr' else 'US'
        print(f"\n{'='*60}")
        print(f"🎯 DÉCOUVERTE VIDÉOS VIRALES - {language.upper()}")
        print(f"{'='*60}")

        # 1. Récupérer les vidéos tendance
        videos = self.get_trending_videos(region_code=region_code, max_results=50)
        print(f"✅ {len(videos)} vidéos tendance récupérées")

        # 2. Filtrer par durée
        videos = self.filter_by_duration(videos)
        print(f"✅ {len(videos)} vidéos < {self.max_duration_minutes} min")

        # 3. Filtrer par âge
        videos = self.filter_by_age(videos)
        print(f"✅ {len(videos)} vidéos < {self.max_age_hours}h")

        if not videos:
            print(f"⚠️  Aucune vidéo ne correspond aux critères")
            return []

        # 4. Calculer les scores de viralité
        print(f"\n📊 Calcul des scores de viralité...")
        for video in tqdm(videos, desc="Analyse"):
            self.calculate_virality_score(video)

        # 5. Trier par score décroissant
        videos.sort(key=lambda v: v['virality_score'], reverse=True)

        # 6. Sélectionner le top N
        top_videos = videos[:top_n]

        # 7. Afficher les résultats
        print(f"\n{'='*60}")
        print(f"🏆 TOP {top_n} VIDÉOS VIRALES - {language.upper()}")
        print(f"{'='*60}\n")

        for i, video in enumerate(top_videos, 1):
            snippet = video['snippet']
            stats = video['statistics']

            print(f"{i}. {snippet['title'][:60]}")
            print(f"   📺 Chaîne: {snippet['channelTitle']}")
            print(f"   🔗 https://youtube.com/watch?v={video['id']}")
            print(f"   📊 Score viral: {video['virality_score']}/100")
            print(f"   👁️  {int(stats['viewCount']):,} vues ({video['views_per_hour']}/h)")
            print(f"   💬 Engagement: {video['engagement_rate']}%")
            print(f"   ⏱️  Durée: {video['duration_minutes']:.1f} min")
            print(f"   🕐 Âge: {video['age_hours']:.1f}h")
            print()

        return top_videos

    def save_results(self, videos_fr, videos_en, output_file='viral_videos.json'):
        """Sauvegarde les résultats dans un fichier JSON"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'french_videos': [],
            'english_videos': []
        }

        for video in videos_fr:
            results['french_videos'].append({
                'id': video['id'],
                'title': video['snippet']['title'],
                'channel': video['snippet']['channelTitle'],
                'url': f"https://youtube.com/watch?v={video['id']}",
                'virality_score': video['virality_score'],
                'views': int(video['statistics']['viewCount']),
                'views_per_hour': video['views_per_hour'],
                'engagement_rate': video['engagement_rate'],
                'duration_minutes': video['duration_minutes'],
                'age_hours': video['age_hours']
            })

        for video in videos_en:
            results['english_videos'].append({
                'id': video['id'],
                'title': video['snippet']['title'],
                'channel': video['snippet']['channelTitle'],
                'url': f"https://youtube.com/watch?v={video['id']}",
                'virality_score': video['virality_score'],
                'views': int(video['statistics']['viewCount']),
                'views_per_hour': video['views_per_hour'],
                'engagement_rate': video['engagement_rate'],
                'duration_minutes': video['duration_minutes'],
                'age_hours': video['age_hours']
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"💾 Résultats sauvegardés dans {output_file}")
        return output_file


def main():
    """Fonction principale"""
    print("🚀 DÉCOUVERTE DE VIDÉOS VIRALES YOUTUBE")
    print("="*60)

    # Initialiser le découvreur
    try:
        discoverer = ViralVideoDiscovery()
    except ValueError as e:
        print(e)
        print("\n💡 Ajoutez votre clé API YouTube dans le fichier .env:")
        print("   YOUTUBE_API_KEY=votre_cle_ici")
        sys.exit(1)

    # Découvrir les vidéos FR
    videos_fr = discoverer.discover_viral_videos(language='fr', top_n=5)

    # Découvrir les vidéos EN
    videos_en = discoverer.discover_viral_videos(language='en', top_n=5)

    # Sauvegarder les résultats
    if videos_fr or videos_en:
        discoverer.save_results(videos_fr, videos_en)

        print(f"\n{'='*60}")
        print(f"✅ DÉCOUVERTE TERMINÉE")
        print(f"   - {len(videos_fr)} vidéos FR")
        print(f"   - {len(videos_en)} vidéos EN")
        print(f"{'='*60}\n")
    else:
        print("⚠️  Aucune vidéo découverte")


if __name__ == '__main__':
    main()
