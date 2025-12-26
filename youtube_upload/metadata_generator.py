#!/usr/bin/env python3
"""
Générateur de métadonnées uniques pour YouTube Shorts
Évite la détection de spam en variant titres, descriptions et tags
"""

import random
import re


class MetadataGenerator:
    """Génère des métadonnées uniques pour chaque vidéo"""

    # Templates de titres FR
    TITLE_TEMPLATES_FR = [
        "{keywords} - Incroyable !",
        "Cette {keywords} va vous choquer",
        "{keywords} que personne ne connaît",
        "La vérité sur {keywords}",
        "{keywords} - Vous n'allez pas y croire",
        "Comment {keywords} en quelques secondes",
        "{keywords} - Révélation choc",
        "Le secret de {keywords} dévoilé",
        "{keywords} qui buzz partout",
        "Découvrez {keywords} maintenant",
    ]

    # Templates de titres EN
    TITLE_TEMPLATES_EN = [
        "{keywords} - Unbelievable!",
        "This {keywords} will shock you",
        "{keywords} nobody knows about",
        "The truth about {keywords}",
        "{keywords} - You won't believe it",
        "How to {keywords} in seconds",
        "{keywords} - Mind-blowing reveal",
        "The secret of {keywords} exposed",
        "{keywords} going viral everywhere",
        "Discover {keywords} now",
    ]

    # Templates de descriptions FR
    DESCRIPTION_TEMPLATES_FR = [
        "🔥 {keywords}\n\n⚡ Abonne-toi pour plus de contenu viral !\n\n#shorts #viral",
        "💡 {keywords}\n\nSuis-moi pour ne rien manquer ! 👇\n\n#pourtoi #trending",
        "🎯 {keywords}\n\n👉 Like et partage si tu as aimé !\n\n#fyp #shorts",
        "✨ {keywords}\n\nActiv la cloche 🔔 pour les prochaines vidéos !\n\n#viral #shorts",
        "🚀 {keywords}\n\nDécouvre plus de contenu incroyable sur ma chaîne !\n\n#trending #fyp",
    ]

    # Templates de descriptions EN
    DESCRIPTION_TEMPLATES_EN = [
        "🔥 {keywords}\n\n⚡ Subscribe for more viral content!\n\n#shorts #viral",
        "💡 {keywords}\n\nFollow me for more! 👇\n\n#foryou #trending",
        "🎯 {keywords}\n\n👉 Like and share if you enjoyed!\n\n#fyp #shorts",
        "✨ {keywords}\n\nTurn on notifications 🔔 for new videos!\n\n#viral #shorts",
        "🚀 {keywords}\n\nCheck out more amazing content on my channel!\n\n#trending #fyp",
    ]

    # Hashtags populaires par langue
    HASHTAGS_FR = [
        ['#shorts', '#viral', '#pourtoi'],
        ['#fyp', '#trending', '#pourtoipage'],
        ['#shorts', '#viralvideo', '#france'],
        ['#tiktok', '#reels', '#shorts'],
        ['#pourtoipage', '#viral', '#trend'],
    ]

    HASHTAGS_EN = [
        ['#shorts', '#viral', '#foryou'],
        ['#fyp', '#trending', '#foryoupage'],
        ['#shorts', '#viralvideo', '#viral'],
        ['#tiktok', '#reels', '#shorts'],
        ['#foryoupage', '#viral', '#trend'],
    ]

    def extract_keywords(self, original_title, max_words=4):
        """
        Extrait les mots-clés importants du titre original

        Args:
            original_title: Titre original de la vidéo YouTube
            max_words: Nombre maximum de mots à extraire

        Returns:
            String de mots-clés
        """
        # Nettoyer le titre
        title = re.sub(r'[^\w\s]', '', original_title.lower())

        # Mots à ignorer
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 'dans', 'sur',
            'official', 'video', 'clip', 'ft', 'feat', 'hd', '4k'
        }

        words = [w for w in title.split() if w not in stop_words and len(w) > 2]
        return ' '.join(words[:max_words])

    def generate_title(self, original_title, language='fr'):
        """
        Génère un titre unique basé sur le titre original

        Args:
            original_title: Titre original de la vidéo
            language: 'fr' ou 'en'

        Returns:
            Titre généré (max 100 caractères pour YouTube)
        """
        keywords = self.extract_keywords(original_title)

        if language == 'fr':
            template = random.choice(self.TITLE_TEMPLATES_FR)
        else:
            template = random.choice(self.TITLE_TEMPLATES_EN)

        title = template.format(keywords=keywords)

        # Limiter à 100 caractères (limite YouTube)
        if len(title) > 100:
            title = title[:97] + '...'

        return title

    def generate_description(self, original_title, language='fr'):
        """
        Génère une description unique

        Args:
            original_title: Titre original de la vidéo
            language: 'fr' ou 'en'

        Returns:
            Description générée
        """
        keywords = self.extract_keywords(original_title)

        if language == 'fr':
            template = random.choice(self.DESCRIPTION_TEMPLATES_FR)
        else:
            template = random.choice(self.DESCRIPTION_TEMPLATES_EN)

        description = template.format(keywords=keywords)

        return description

    def generate_tags(self, original_title, language='fr'):
        """
        Génère des tags uniques

        Args:
            original_title: Titre original de la vidéo
            language: 'fr' ou 'en'

        Returns:
            Liste de tags
        """
        # Tags basés sur les mots-clés
        keywords = self.extract_keywords(original_title, max_words=3)
        keyword_tags = [f"#{word}" for word in keywords.split()]

        # Tags populaires aléatoires
        if language == 'fr':
            popular_tags = random.choice(self.HASHTAGS_FR)
        else:
            popular_tags = random.choice(self.HASHTAGS_EN)

        # Combiner (max 15 tags pour YouTube)
        all_tags = keyword_tags + popular_tags
        return list(set(all_tags))[:15]  # Dédupliquer et limiter

    def generate_all_metadata(self, original_title, language='fr'):
        """
        Génère toutes les métadonnées d'un coup

        Args:
            original_title: Titre original de la vidéo
            language: 'fr' ou 'en'

        Returns:
            Dict avec title, description, tags
        """
        return {
            'title': self.generate_title(original_title, language),
            'description': self.generate_description(original_title, language),
            'tags': self.generate_tags(original_title, language),
            'category': '22',  # People & Blogs (catégorie virale)
            'privacy_status': 'public',
        }


def main():
    """Test du générateur de métadonnées"""
    generator = MetadataGenerator()

    test_titles = [
        "10 Life Hacks You Need to Know",
        "Les 10 astuces que tout le monde devrait connaître",
    ]

    print("\n" + "="*70)
    print("TEST DU GÉNÉRATEUR DE MÉTADONNÉES")
    print("="*70)

    for title in test_titles:
        lang = 'en' if 'Life' in title else 'fr'
        print(f"\n📹 Titre original: {title}")
        print(f"🌍 Langue: {lang.upper()}")
        print("-"*70)

        metadata = generator.generate_all_metadata(title, lang)

        print(f"✏️  Titre généré: {metadata['title']}")
        print(f"📝 Description:\n{metadata['description']}")
        print(f"🏷️  Tags: {', '.join(metadata['tags'])}")
        print("="*70)


if __name__ == '__main__':
    main()
