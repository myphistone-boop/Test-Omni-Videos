#!/usr/bin/env python3
"""
Pipeline complet d'automatisation de vidéos virales
- Découverte automatique de vidéos virales YouTube
- Interface interactive pour sélection/téléchargement
- Traitement automatique en shorts TikTok
"""

import os
import sys
import json
from pathlib import Path
from discover_viral_videos import ViralVideoDiscovery
from create_subtitled_video import process_video
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def print_banner():
    """Affiche le banner du programme"""
    print("\n" + "="*70)
    print(" 🎬 AUTOMATISATION VIDÉOS VIRALES YOUTUBE → TIKTOK")
    print("="*70)


def print_menu():
    """Affiche le menu principal"""
    print("\n📋 MENU PRINCIPAL:")
    print("  1. 🔍 Découvrir les vidéos virales (5 FR + 5 EN)")
    print("  2. 📥 Télécharger et traiter les vidéos sélectionnées")
    print("  3. 📊 Afficher les derniers résultats")
    print("  4. ❌ Quitter")
    print()


def discover_videos():
    """Lance la découverte de vidéos virales"""
    print_banner()
    print("🚀 LANCEMENT DE LA DÉCOUVERTE...")

    try:
        discoverer = ViralVideoDiscovery()

        # Découvrir les vidéos FR
        videos_fr = discoverer.discover_viral_videos(language='fr', top_n=5)

        # Découvrir les vidéos EN
        videos_en = discoverer.discover_viral_videos(language='en', top_n=5)

        # Sauvegarder les résultats
        if videos_fr or videos_en:
            output_file = discoverer.save_results(videos_fr, videos_en)

            print(f"\n{'='*70}")
            print(f"✅ DÉCOUVERTE TERMINÉE")
            print(f"   - {len(videos_fr)} vidéos FR découvertes")
            print(f"   - {len(videos_en)} vidéos EN découvertes")
            print(f"   - Résultats sauvegardés dans {output_file}")
            print(f"{'='*70}")

            return True
        else:
            print("⚠️  Aucune vidéo découverte")
            return False

    except ValueError as e:
        print(f"❌ Erreur: {e}")
        print("\n💡 Assurez-vous d'avoir configuré votre clé API YouTube dans .env:")
        print("   YOUTUBE_API_KEY=votre_cle_ici")
        return False

    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False


def load_results(results_file='viral_videos.json'):
    """Charge les résultats de découverte"""
    if not os.path.exists(results_file):
        print(f"❌ Fichier {results_file} introuvable")
        print("   Lancez d'abord la découverte (option 1)")
        return None

    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def display_results():
    """Affiche les derniers résultats de découverte"""
    results = load_results()
    if not results:
        return

    print_banner()
    print(f"📊 DERNIERS RÉSULTATS ({results['timestamp'][:19]})")
    print("="*70)

    # Vidéos FR
    print("\n🇫🇷 VIDÉOS FRANÇAISES:")
    for i, video in enumerate(results['french_videos'], 1):
        print(f"\n{i}. {video['title'][:60]}")
        print(f"   📺 {video['channel']}")
        print(f"   🔗 {video['url']}")
        print(f"   📊 Score: {video['virality_score']}/100 | "
              f"👁️  {video['views']:,} vues | "
              f"⏱️  {video['duration_minutes']:.1f} min")

    # Vidéos EN
    print("\n🇺🇸 VIDÉOS ANGLAISES:")
    for i, video in enumerate(results['english_videos'], 1):
        print(f"\n{i}. {video['title'][:60]}")
        print(f"   📺 {video['channel']}")
        print(f"   🔗 {video['url']}")
        print(f"   📊 Score: {video['virality_score']}/100 | "
              f"👁️  {video['views']:,} vues | "
              f"⏱️  {video['duration_minutes']:.1f} min")

    print("\n" + "="*70)


def select_videos_to_process():
    """Permet de sélectionner les vidéos à traiter"""
    results = load_results()
    if not results:
        return []

    print_banner()
    print("📥 SÉLECTION DES VIDÉOS À TRAITER")
    print("="*70)

    all_videos = results['french_videos'] + results['english_videos']

    print(f"\nTotal: {len(all_videos)} vidéos disponibles")
    print("\nOptions:")
    print("  1. Traiter TOUTES les vidéos (10 vidéos)")
    print("  2. Traiter uniquement les vidéos FR (5 vidéos)")
    print("  3. Traiter uniquement les vidéos EN (5 vidéos)")
    print("  4. Sélection manuelle")
    print("  5. Retour au menu")

    choice = input("\n👉 Votre choix (1-5): ").strip()

    if choice == '1':
        return all_videos
    elif choice == '2':
        return results['french_videos']
    elif choice == '3':
        return results['english_videos']
    elif choice == '4':
        return manual_selection(all_videos)
    else:
        return []


def manual_selection(videos):
    """Sélection manuelle des vidéos"""
    print("\n📋 VIDÉOS DISPONIBLES:")
    for i, video in enumerate(videos, 1):
        print(f"  {i}. {video['title'][:50]} (Score: {video['virality_score']}/100)")

    print("\nEntrez les numéros des vidéos à traiter (séparés par des virgules)")
    print("Exemple: 1,3,5,7")

    selection = input("\n👉 Votre sélection: ").strip()

    if not selection:
        return []

    try:
        indices = [int(x.strip()) - 1 for x in selection.split(',')]
        selected = [videos[i] for i in indices if 0 <= i < len(videos)]
        return selected
    except (ValueError, IndexError):
        print("❌ Sélection invalide")
        return []


def process_selected_videos():
    """Traite les vidéos sélectionnées"""
    selected_videos = select_videos_to_process()

    if not selected_videos:
        print("\n⚠️  Aucune vidéo sélectionnée")
        return

    print(f"\n{'='*70}")
    print(f"🎬 TRAITEMENT DE {len(selected_videos)} VIDÉO(S)")
    print(f"{'='*70}")

    # Confirmation
    print(f"\nVous allez traiter {len(selected_videos)} vidéo(s):")
    for i, video in enumerate(selected_videos, 1):
        print(f"  {i}. {video['title'][:60]}")

    confirm = input("\n👉 Confirmer ? (o/N): ").strip().lower()

    if confirm != 'o':
        print("❌ Traitement annulé")
        return

    # Créer le dossier de sortie
    output_dir = Path('output_shorts')
    output_dir.mkdir(exist_ok=True)

    # Traiter chaque vidéo
    success_count = 0
    fail_count = 0

    for i, video in enumerate(selected_videos, 1):
        print(f"\n{'='*70}")
        print(f"📹 TRAITEMENT {i}/{len(selected_videos)}: {video['title'][:50]}")
        print(f"{'='*70}")

        try:
            # Nom de sortie basé sur le titre
            safe_title = "".join(c for c in video['title'] if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_file = output_dir / f"{safe_title}.mp4"

            # Lancer le traitement
            print(f"\n🔗 URL: {video['url']}")
            result = process_video(video['url'], str(output_file))

            if result:
                success_count += 1
                print(f"✅ Vidéo {i}/{len(selected_videos)} traitée avec succès")
            else:
                fail_count += 1
                print(f"❌ Échec du traitement de la vidéo {i}/{len(selected_videos)}")

        except Exception as e:
            fail_count += 1
            print(f"❌ Erreur lors du traitement: {e}")

    # Résumé final
    print(f"\n{'='*70}")
    print(f"📊 RÉSUMÉ DU TRAITEMENT")
    print(f"{'='*70}")
    print(f"✅ Succès: {success_count}/{len(selected_videos)}")
    print(f"❌ Échecs: {fail_count}/{len(selected_videos)}")
    print(f"📁 Dossier de sortie: {output_dir.absolute()}")
    print(f"{'='*70}\n")


def main():
    """Fonction principale du pipeline"""
    print_banner()

    while True:
        print_menu()
        choice = input("👉 Votre choix (1-4): ").strip()

        if choice == '1':
            discover_videos()

        elif choice == '2':
            process_selected_videos()

        elif choice == '3':
            display_results()

        elif choice == '4':
            print("\n👋 Au revoir!")
            sys.exit(0)

        else:
            print("❌ Choix invalide. Réessayez.")

        input("\n⏸️  Appuyez sur Entrée pour continuer...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programme interrompu. Au revoir!")
        sys.exit(0)
