#!/usr/bin/env python3
"""
Module de découverte de vidéos virales YouTube (optimisé pour la crème de la crème)
- Recherche les vidéos tendance des 48 dernières heures
- Filtre par durée (<15 min)
- Calcule un score de viralité optimisé (propagation 60%, engagement 30%, fraîcheur 10%)
- Sélectionne top 5 FR + top 5 EN parmi 200 vidéos tendance
"""

import os
import sys
from datetime import datetime, timedelta, timezone
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

        # Créer un client HTTP sans vérification SSL (même approche que pour OpenAI)
        # Nécessaire pour contourner les proxies/antivirus d'entreprise
        http = httplib2.Http()
        http.disable_ssl_certificate_validation = True

        self.youtube = build('youtube', 'v3', developerKey=self.api_key, http=http)
        self.max_duration_minutes = 15
        self.max_age_hours = 48  # 48h pour la crème de la crème des vidéos virales

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

        except HttpError as e:
            print(f"❌ Erreur API YouTube: {e}")
            return []

        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return []

    def filter_music(self, videos):
        """Filtre les vidéos musicales et clips"""
        filtered = []

        # Mots-clés à exclure dans le titre ou la description
        music_keywords = [
            'official video', 'official music video', 'music video',
            'official audio', 'official mv', 'lyric video', 'lyrics',
            '(official)', '[official]', 'mv', 'vevo', 'topic',
            'full album', 'audio official', 'visualizer'
        ]

        # Suffixes de chaînes à exclure
        channel_suffixes = ['- Topic', 'VEVO', 'Topic', 'Records']

        for video in videos:
            snippet = video['snippet']
            title = snippet['title'].lower()
            channel_title = snippet['channelTitle']
            category_id = snippet.get('categoryId', '')

            # Exclure si c'est dans la catégorie Music (10)
            if category_id == '10':
                continue

            # Exclure si le titre contient des mots-clés musicaux
            if any(keyword in title for keyword in music_keywords):
                continue

            # Exclure si la chaîne se termine par des suffixes musicaux
            if any(channel_title.endswith(suffix) for suffix in channel_suffixes):
                continue

            filtered.append(video)

        return filtered

    def filter_non_shortable(self, videos):
        """Filtre les vidéos non adaptées pour des shorts TikTok"""
        filtered = []

        # Mots-clés de contenus NON shortables
        excluded_keywords = [
            # Trailers & Teasers (uniquement officiels)
            'official trailer', 'movie trailer', 'game trailer',
            'teaser officiel', 'bande-annonce officielle',
            'coming soon trailer', 'announce trailer', 'reveal trailer',

            # Lives & Streams (uniquement les formats longs)
            'livestream', 'live stream', 'en direct',
            'streaming now', 'replay', 'rediffusion',
            'full stream', 'vod', 'twitch replay',
            '🔴 live', '[live]', '(live)',

            # Podcasts & Interviews longues (formats complets uniquement)
            'full podcast', 'podcast complet', 'full episode', 'episode complet',
            'full interview', 'interview complète', 'interview intégrale',
            'épisode complet', 'intégrale',

            # Sport en direct
            'full match', 'match complet', 'full game',
            'highlights extended', 'extended highlights',
            'match en entier', 'football match', 'basketball game',

            # Conférences & Webinaires
            'conference', 'webinar', 'webinaire',
            'keynote', 'présentation complète',
            'full presentation', 'full talk',

            # Gaming longue durée
            'full gameplay', 'gameplay complet',
            'let\'s play', 'playthrough', 'walkthrough',
            'no commentary', 'full game',

            # Divers non shortables (formats longs uniquement)
            'full documentary', 'documentaire complet',
            'full movie', 'film complet', 'film entier',
            'full concert', 'concert complet', 'concert entier',
            'study with me', 'asmr 1 hour', 'meditation 1 hour',
            'sleep music 1 hour', 'relaxing music 1 hour',

            # Formats trop longs
            '1 hour', '2 hours', '3 hours',
            '1h', '2h', '3h',
            'compilation 1h', 'best of 1h',
        ]

        # Catégories à exclure (IDs YouTube)
        excluded_categories = [
            '17',  # Sports (matchs complets, highlights longs)
            # Note: Catégorie 24 (Entertainment) retirée - trop large, exclut du bon contenu viral
        ]

        for video in videos:
            snippet = video['snippet']
            title = snippet['title'].lower()
            description = snippet.get('description', '').lower()[:200]  # Premiers 200 chars
            category_id = snippet.get('categoryId', '')

            # Exclure si catégorie non désirée
            if category_id in excluded_categories:
                continue

            # Exclure si le titre contient des mots-clés exclus
            if any(keyword in title for keyword in excluded_keywords):
                continue

            # Exclure si la description contient certains mots-clés critiques (très restrictifs)
            critical_keywords = ['official trailer', 'livestream', 'full episode', 'full podcast']
            if any(keyword in description for keyword in critical_keywords):
                continue

            filtered.append(video)

        return filtered

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
        now = datetime.now(timezone.utc)
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
        Calcule le score de viralité d'une vidéo (optimisé pour la crème de la crème)

        Score = (Propagation * 0.6) + (Engagement * 0.3) + (Fraîcheur * 0.1)

        - Propagation : vues/heure (poids augmenté - meilleur indicateur de viralité)
        - Engagement : (likes + comments) / vues (normalisé)
        - Fraîcheur : bonus pour vidéos très récentes (<24h)
        """
        stats = video.get('statistics', {})

        # Récupérer les métriques
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        age_hours = video.get('age_hours', 48)

        # Éviter division par zéro
        if age_hours == 0:
            age_hours = 0.1
        if views == 0:
            return 0

        # 1. Score de propagation (vues/heure) - POIDS AUGMENTÉ
        views_per_hour = views / age_hours
        # Normalisation progressive pour mieux différencier les vraies vidéos virales
        if views_per_hour < 1000:
            propagation_score = views_per_hour / 100  # 0-10
        elif views_per_hour < 10000:
            propagation_score = 10 + (views_per_hour - 1000) / 180  # 10-60
        else:
            propagation_score = 60 + min((views_per_hour - 10000) / 1000, 40)  # 60-100

        propagation_score = min(propagation_score, 100)

        # 2. Score d'engagement - mieux adapté pour les vraies vidéos virales
        engagement_rate = (likes + comments) / views
        # Les vidéos virales ont généralement 2-5% d'engagement
        engagement_score = min(engagement_rate * 2000, 100)  # Plus sensible

        # 3. Score de fraîcheur - adapté pour 48h
        if age_hours < 24:
            freshness_score = 100  # Très frais
        elif age_hours < 48:
            freshness_score = 75   # Encore frais
        else:
            freshness_score = 50   # Moins frais

        # Score final - POIDS OPTIMISÉS POUR LA VIRALITÉ
        final_score = (
            propagation_score * 0.6 +  # Augmenté de 0.5 à 0.6
            engagement_score * 0.3 +   # Réduit de 0.4 à 0.3
            freshness_score * 0.1      # Maintenu à 0.1
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

        # 1. Récupérer le maximum de vidéos tendance pour sélectionner la crème de la crème
        videos = self.get_trending_videos(region_code=region_code, max_results=200)
        print(f"✅ {len(videos)} vidéos tendance récupérées")

        # 2. Filtrer les vidéos musicales/clips
        videos = self.filter_music(videos)
        print(f"✅ {len(videos)} vidéos (musique exclue)")

        # 3. Filtrer les contenus non shortables (trailers, lives, etc.)
        videos = self.filter_non_shortable(videos)
        print(f"✅ {len(videos)} vidéos (shortables uniquement)")

        # 4. Filtrer par durée
        videos = self.filter_by_duration(videos)
        print(f"✅ {len(videos)} vidéos < {self.max_duration_minutes} min")

        # 5. Filtrer par âge avec fallback progressif
        # Optimisé pour la crème de la crème : 48h par défaut
        age_limits = [48, 72, 168]  # 48h, 72h, 1 semaine
        filtered_videos = []

        for age_limit in age_limits:
            self.max_age_hours = age_limit
            filtered_videos = self.filter_by_age(videos)

            if len(filtered_videos) >= top_n:
                print(f"✅ {len(filtered_videos)} vidéos < {age_limit}h")
                break
            elif age_limit == age_limits[-1]:
                # Dernière tentative, on prend ce qu'on a
                print(f"⚠️  Seulement {len(filtered_videos)} vidéos < {age_limit}h (critères assouplis)")

        videos = filtered_videos

        if not videos:
            print(f"⚠️  Aucune vidéo ne correspond aux critères")
            return []

        # 6. Calculer les scores de viralité
        print(f"\n📊 Calcul des scores de viralité...")
        for video in tqdm(videos, desc="Analyse"):
            self.calculate_virality_score(video)

        # 7. Trier par score décroissant
        videos.sort(key=lambda v: v['virality_score'], reverse=True)

        # 8. Sélectionner le top N
        top_videos = videos[:top_n]

        # Vérifier si on a assez de vidéos
        if len(top_videos) < top_n:
            print(f"⚠️  Seulement {len(top_videos)} vidéos trouvées (objectif: {top_n})")

        # 9. Afficher les résultats
        print(f"\n{'='*60}")
        print(f"🏆 TOP {top_n} VIDÉOS VIRALES - {language.upper()}")
        print(f"{'='*60}\n")

        for i, video in enumerate(top_videos, 1):
            snippet = video['snippet']
            stats = video['statistics']

            # Limiter le titre à 6 mots
            title_words = snippet['title'].split()[:6]
            short_title = ' '.join(title_words)
            if len(snippet['title'].split()) > 6:
                short_title += "..."

            print(f"{i}. {short_title} - 📺 {snippet['channelTitle']}")
            print(f"   🔗 https://youtube.com/watch?v={video['id']}")
            print(f"   📊 Score: {video['virality_score']}/100 | 👁️  {int(stats['viewCount']):,} vues | ⏱️  {video['duration_minutes']:.1f} min | 🕐 {video['age_hours']:.1f}h")
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
