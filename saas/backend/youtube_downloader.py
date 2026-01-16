#!/usr/bin/env python3
"""
Script simple pour télécharger des vidéos YouTube
"""

import yt_dlp
import os


def telecharger_video(url, output_path=None, cookies_path=None):
    """
    Télécharge une vidéo YouTube à partir de son URL

    Args:
        url (str): L'URL de la vidéo YouTube
        output_path (str): Chemin de sortie (optionnel, sinon videos_telechargees/)
        cookies_path (str): Chemin vers cookies.txt (optionnel)
    """
    # Créer un dossier pour les téléchargements s'il n'existe pas
    dossier_telechargement = "videos_telechargees"
    if not os.path.exists(dossier_telechargement):
        os.makedirs(dossier_telechargement)

    # Configuration des options de téléchargement
    options = {
        'format': 'best',  # Meilleure qualité disponible
        'outtmpl': output_path if output_path else f'{dossier_telechargement}/%(title)s.%(ext)s',  # Nom du fichier
        'quiet': False,  # Afficher la progression
        'no_warnings': False,
        'nocheckcertificate': True,  # Désactiver vérification SSL (nécessaire sur PC d'entreprise avec proxy)
    }

    # Ajouter cookies si fournis
    if cookies_path and os.path.exists(cookies_path):
        options['cookiefile'] = cookies_path
        print(f"🍪 Utilisation des cookies: {cookies_path}")

    try:
        print(f"\n🎬 Téléchargement de la vidéo depuis : {url}")
        print("-" * 60)

        final_path = None
        with yt_dlp.YoutubeDL(options) as ydl:
            # Récupérer les informations et télécharger
            info = ydl.extract_info(url, download=True)
            titre = info.get('title', 'Titre inconnu')
            duree = info.get('duration', 0)

            print(f"📝 Titre : {titre}")
            print(f"⏱️  Durée : {duree // 60}:{duree % 60:02d}")

            # Obtenir le vrai nom du fichier téléchargé (avec la bonne extension)
            final_path = ydl.prepare_filename(info)

        # Vérifier que le fichier existe et n'est pas vide
        if not os.path.exists(final_path):
            raise FileNotFoundError(f"Le fichier téléchargé n'existe pas : {final_path}")

        file_size = os.path.getsize(final_path)
        if file_size == 0:
            os.remove(final_path)  # Supprimer le fichier vide
            raise Exception(
                "Le téléchargement a échoué (fichier vide). "
                "Vérifiez que vos cookies YouTube sont valides et à jour. "
                "La vidéo est peut-être protégée ou nécessite une connexion."
            )

        print(f"\n✅ Téléchargement terminé : {final_path} ({file_size / 1024 / 1024:.1f} MB)")
        return final_path

    except Exception as e:
        print(f"\n❌ Erreur lors du téléchargement : {e}")
        raise


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🎥  TÉLÉCHARGEUR DE VIDÉOS YOUTUBE  🎥")
    print("=" * 60)

    # Demander l'URL à l'utilisateur
    url = input("\n📎 Entrez l'URL de la vidéo YouTube : ").strip()

    if not url:
        print("❌ Erreur : URL vide. Veuillez entrer une URL valide.")
        return

    # Télécharger la vidéo
    telecharger_video(url)


if __name__ == "__main__":
    main()
