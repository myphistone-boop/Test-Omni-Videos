"""
Cookie Monitor - Système de surveillance des cookies YouTube
Vérifie la validité des cookies et maintient un statut en temps réel
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import yt_dlp

# Paths
COOKIE_DIR = Path("/home/shorts/cookies")
COOKIE_FILE = COOKIE_DIR / "account_1.txt"
STATUS_FILE = Path("/home/shorts/cookie_status.json")

# Ensure directories exist
COOKIE_DIR.mkdir(parents=True, exist_ok=True)


class CookieStatus:
    """Classe pour gérer le statut du cookie"""

    def __init__(self):
        self.status_file = STATUS_FILE

    def get_status(self) -> Dict:
        """
        Récupère le statut actuel du cookie

        Returns:
            {
                "status": "ok" | "invalid" | "warning" | "missing",
                "last_check": "2026-01-14T10:30:00",
                "last_success": "2026-01-14T10:30:00",
                "created_at": "2026-01-14T08:00:00",
                "message": "Cookie valide",
                "age_hours": 2.5,
                "health_score": 100
            }
        """
        if not self.status_file.exists():
            return {
                "status": "missing",
                "message": "Aucun cookie configuré",
                "last_check": None,
                "last_success": None,
                "created_at": None,
                "age_hours": 0,
                "health_score": 0
            }

        try:
            with open(self.status_file, 'r') as f:
                data = json.load(f)

            # Calculer l'âge du cookie
            if data.get('created_at'):
                created = datetime.fromisoformat(data['created_at'])
                age_hours = (datetime.now() - created).total_seconds() / 3600
                data['age_hours'] = round(age_hours, 1)

            # Calculer le health score
            data['health_score'] = self._calculate_health_score(data)

            return data
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur de lecture du statut: {str(e)}",
                "last_check": None,
                "last_success": None,
                "created_at": None,
                "age_hours": 0,
                "health_score": 0
            }

    def _calculate_health_score(self, data: Dict) -> int:
        """
        Calcule un score de santé 0-100

        Critères:
        - Cookie récent: +40 points
        - Dernière vérification récente: +30 points
        - Statut OK: +30 points
        """
        score = 0

        # Status OK = 30 points
        if data.get('status') == 'ok':
            score += 30

        # Dernière vérification < 3h = 30 points
        if data.get('last_check'):
            last_check = datetime.fromisoformat(data['last_check'])
            hours_since_check = (datetime.now() - last_check).total_seconds() / 3600
            if hours_since_check < 3:
                score += 30
            elif hours_since_check < 24:
                score += 15

        # Cookie < 7 jours = 40 points
        if data.get('created_at'):
            created = datetime.fromisoformat(data['created_at'])
            days_old = (datetime.now() - created).days
            if days_old < 7:
                score += 40
            elif days_old < 30:
                score += 20

        return min(score, 100)

    def update_status(self, status: str, message: str, is_success: bool = True):
        """
        Met à jour le statut du cookie

        Args:
            status: "ok", "invalid", "warning", "missing"
            message: Message descriptif
            is_success: Si True, met à jour last_success
        """
        now = datetime.now().isoformat()

        # Charger le statut existant
        existing = {}
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    existing = json.load(f)
            except:
                pass

        # Préparer les nouvelles données
        data = {
            "status": status,
            "message": message,
            "last_check": now,
            "last_success": now if is_success else existing.get('last_success'),
            "created_at": existing.get('created_at', now)  # Garder la date de création
        }

        # Sauvegarder
        with open(self.status_file, 'w') as f:
            json.dump(data, f, indent=2)

    def mark_cookie_created(self):
        """Marque qu'un nouveau cookie a été créé"""
        now = datetime.now().isoformat()
        data = {
            "status": "ok",
            "message": "Cookie uploadé avec succès",
            "last_check": now,
            "last_success": now,
            "created_at": now
        }
        with open(self.status_file, 'w') as f:
            json.dump(data, f, indent=2)


def check_cookie_validity(cookie_path: str = None) -> Dict:
    """
    Vérifie si le cookie est valide en tentant un téléchargement test

    Args:
        cookie_path: Chemin vers le fichier cookie (par défaut: COOKIE_FILE)

    Returns:
        {
            "valid": True/False,
            "message": "...",
            "error": "..." (si échec)
        }
    """
    if cookie_path is None:
        cookie_path = str(COOKIE_FILE)

    # Vérifier que le fichier existe
    if not os.path.exists(cookie_path):
        return {
            "valid": False,
            "message": "Fichier cookie introuvable",
            "error": "Cookie file not found"
        }

    # Test avec une vidéo YouTube simple
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" (première vidéo YouTube)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookie_path,
        'extract_flat': True,  # Ne télécharge pas, juste extrait les métadonnées
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

            if info:
                return {
                    "valid": True,
                    "message": "Cookie valide et fonctionnel",
                    "error": None
                }
            else:
                return {
                    "valid": False,
                    "message": "Impossible d'extraire les informations vidéo",
                    "error": "No video info"
                }

    except Exception as e:
        error_msg = str(e).lower()

        # Détecter les erreurs spécifiques
        if 'sign in' in error_msg or 'login' in error_msg:
            return {
                "valid": False,
                "message": "Cookie expiré ou invalide (authentification requise)",
                "error": str(e)
            }
        elif 'bot' in error_msg:
            return {
                "valid": False,
                "message": "Détection bot par YouTube",
                "error": str(e)
            }
        elif '403' in error_msg or 'forbidden' in error_msg:
            return {
                "valid": False,
                "message": "Accès refusé (cookie possiblement banni)",
                "error": str(e)
            }
        else:
            return {
                "valid": False,
                "message": f"Erreur lors de la vérification: {str(e)}",
                "error": str(e)
            }


def monitor_cookie():
    """
    Fonction principale de monitoring
    À appeler via cron job toutes les 1-3 heures
    """
    print(f"🔍 Vérification du cookie à {datetime.now()}")

    monitor = CookieStatus()

    # Vérifier la validité
    result = check_cookie_validity()

    if result['valid']:
        print("✅ Cookie valide")
        monitor.update_status('ok', result['message'], is_success=True)
    else:
        print(f"❌ Cookie invalide: {result['message']}")
        monitor.update_status('invalid', result['message'], is_success=False)

    # Afficher le statut complet
    status = monitor.get_status()
    print(f"📊 Health Score: {status['health_score']}/100")
    print(f"⏰ Âge du cookie: {status.get('age_hours', 0):.1f} heures")


if __name__ == "__main__":
    # Test du monitoring
    monitor_cookie()
