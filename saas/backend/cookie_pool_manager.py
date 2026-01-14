"""
Cookie Pool Manager - Gestion centralisée des cookies YouTube
Rotation intelligente + Rate limiting + Health monitoring
"""

import os
import time
import threading
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json


class CookieAccount:
    """Représente un compte YouTube avec ses cookies"""

    def __init__(self, account_id: str, cookies_path: str, max_requests_per_hour: int = 100):
        self.account_id = account_id
        self.cookies_path = cookies_path
        self.max_requests_per_hour = max_requests_per_hour

        # Rate limiting
        self.request_history: List[datetime] = []

        # Health monitoring
        self.is_healthy = True
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_success = datetime.now()
        self.quarantine_until: Optional[datetime] = None

        # Stats
        self.total_requests = 0
        self.total_errors = 0
        self.created_at = datetime.now()

    def can_make_request(self) -> bool:
        """Vérifie si ce compte peut faire une requête (rate limiting + health)"""

        # Vérifier si en quarantaine
        if self.quarantine_until and datetime.now() < self.quarantine_until:
            return False

        # Vérifier si healthy
        if not self.is_healthy:
            return False

        # Vérifier si le fichier cookies existe
        if not Path(self.cookies_path).exists():
            self.is_healthy = False
            self.last_error = "Fichier cookies introuvable"
            return False

        # Nettoyer l'historique (garder seulement dernière heure)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        self.request_history = [
            req_time for req_time in self.request_history
            if req_time > one_hour_ago
        ]

        # Vérifier le rate limit
        if len(self.request_history) >= self.max_requests_per_hour:
            return False

        return True

    def record_request(self, success: bool, error_msg: str = None):
        """Enregistre une requête (succès ou échec)"""

        self.request_history.append(datetime.now())
        self.total_requests += 1

        if success:
            self.error_count = 0
            self.last_success = datetime.now()
            self.last_error = None

            # Sortir de quarantaine si succès
            self.quarantine_until = None

        else:
            self.total_errors += 1
            self.error_count += 1
            self.last_error = error_msg

            # Si 3 erreurs consécutives → quarantaine 1h
            if self.error_count >= 3:
                self.quarantine_until = datetime.now() + timedelta(hours=1)
                print(f"⚠️  Compte {self.account_id} mis en quarantaine jusqu'à {self.quarantine_until}")

            # Si erreur 403/429 (ban) → quarantaine immédiate 2h
            if error_msg and ("403" in error_msg or "429" in error_msg or "bot" in error_msg.lower()):
                self.quarantine_until = datetime.now() + timedelta(hours=2)
                print(f"🚨 Compte {self.account_id} banni temporairement (quarantaine 2h)")

    def get_stats(self) -> Dict:
        """Retourne les statistiques du compte"""
        return {
            "account_id": self.account_id,
            "is_healthy": self.is_healthy,
            "in_quarantine": self.quarantine_until is not None and datetime.now() < self.quarantine_until,
            "quarantine_until": self.quarantine_until.isoformat() if self.quarantine_until else None,
            "requests_last_hour": len(self.request_history),
            "max_requests_per_hour": self.max_requests_per_hour,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": f"{(self.total_errors / max(self.total_requests, 1)) * 100:.1f}%",
            "last_success": self.last_success.isoformat(),
            "last_error": self.last_error,
            "uptime_hours": (datetime.now() - self.created_at).total_seconds() / 3600
        }


class CookiePoolManager:
    """Gestionnaire centralisé du pool de cookies YouTube"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern - une seule instance du pool"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialise le pool de cookies"""

        # Éviter double initialisation (singleton)
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.accounts: List[CookieAccount] = []
        self.current_index = 0

        # Configuration
        self.cookies_dir = Path("/home/shorts/cookie_pool")
        self.max_requests_per_hour = 100  # Par compte

        # Stats globales
        self.total_requests = 0
        self.total_success = 0
        self.total_failures = 0
        self.started_at = datetime.now()

        print("🔧 Initialisation du Cookie Pool Manager...")
        self._load_cookie_accounts()

    def _load_cookie_accounts(self):
        """Charge tous les comptes du pool depuis le répertoire cookies"""

        # Créer le répertoire si n'existe pas
        self.cookies_dir.mkdir(parents=True, exist_ok=True)

        # Charger tous les fichiers cookies_*.txt
        cookie_files = sorted(self.cookies_dir.glob("cookies_*.txt"))

        if not cookie_files:
            print("⚠️  ATTENTION: Aucun fichier cookies trouvé dans", self.cookies_dir)
            print("   Créez des fichiers: cookies_1.txt, cookies_2.txt, etc.")
            print("   Le pool fonctionnera en mode dégradé (fallback Whisper)")
            return

        for cookie_file in cookie_files:
            account_id = cookie_file.stem  # "cookies_1" → "cookies_1"
            account = CookieAccount(
                account_id=account_id,
                cookies_path=str(cookie_file),
                max_requests_per_hour=self.max_requests_per_hour
            )
            self.accounts.append(account)
            print(f"   ✅ Compte chargé: {account_id} ({cookie_file})")

        print(f"✅ Pool initialisé avec {len(self.accounts)} compte(s)")

    def get_cookie_path(self) -> Optional[str]:
        """
        Récupère le chemin vers un fichier cookies disponible (rotation round-robin)

        Returns:
            str: Chemin vers cookies.txt ou None si aucun disponible
        """

        if not self.accounts:
            print("⚠️  Aucun compte dans le pool - fallback nécessaire")
            return None

        # Essayer jusqu'à len(accounts) fois (rotation complète)
        attempts = 0
        max_attempts = len(self.accounts)

        while attempts < max_attempts:
            # Rotation round-robin
            account = self.accounts[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.accounts)

            # Vérifier si le compte peut faire une requête
            if account.can_make_request():
                print(f"🔄 Utilisation du compte: {account.account_id}")
                print(f"   Requêtes dernière heure: {len(account.request_history)}/{account.max_requests_per_hour}")
                return account.cookies_path

            attempts += 1

        # Aucun compte disponible
        print("⚠️  Tous les comptes sont saturés ou en quarantaine")
        self._print_pool_status()
        return None

    def record_result(self, cookies_path: str, success: bool, error_msg: str = None):
        """
        Enregistre le résultat d'une requête

        Args:
            cookies_path: Chemin du fichier cookies utilisé
            success: True si succès, False si échec
            error_msg: Message d'erreur si échec
        """

        # Trouver le compte correspondant
        for account in self.accounts:
            if account.cookies_path == cookies_path:
                account.record_request(success, error_msg)

                # Stats globales
                self.total_requests += 1
                if success:
                    self.total_success += 1
                else:
                    self.total_failures += 1

                break

    def get_pool_stats(self) -> Dict:
        """Retourne les statistiques globales du pool"""

        healthy_accounts = sum(1 for acc in self.accounts if acc.is_healthy)
        quarantined_accounts = sum(
            1 for acc in self.accounts
            if acc.quarantine_until and datetime.now() < acc.quarantine_until
        )

        return {
            "total_accounts": len(self.accounts),
            "healthy_accounts": healthy_accounts,
            "quarantined_accounts": quarantined_accounts,
            "total_requests": self.total_requests,
            "total_success": self.total_success,
            "total_failures": self.total_failures,
            "success_rate": f"{(self.total_success / max(self.total_requests, 1)) * 100:.1f}%",
            "uptime_hours": (datetime.now() - self.started_at).total_seconds() / 3600,
            "accounts": [acc.get_stats() for acc in self.accounts]
        }

    def _print_pool_status(self):
        """Affiche le status du pool dans la console"""

        print("\n" + "="*60)
        print("📊 STATUS DU COOKIE POOL")
        print("="*60)

        for account in self.accounts:
            status = "✅" if account.can_make_request() else "❌"
            quarantine = ""
            if account.quarantine_until and datetime.now() < account.quarantine_until:
                remaining = (account.quarantine_until - datetime.now()).total_seconds() / 60
                quarantine = f" (Quarantaine: {remaining:.0f}min)"

            print(f"{status} {account.account_id}: "
                  f"{len(account.request_history)}/{account.max_requests_per_hour} req/h"
                  f"{quarantine}")

        print("="*60 + "\n")

    def reload_accounts(self):
        """Recharge les comptes (après refresh des cookies)"""
        print("🔄 Rechargement des comptes du pool...")
        self.accounts.clear()
        self.current_index = 0
        self._load_cookie_accounts()

    def add_random_delay(self):
        """Ajoute un délai aléatoire pour simuler comportement humain"""
        import random
        delay = random.uniform(2, 5)  # 2-5 secondes
        time.sleep(delay)


# Instance globale (singleton)
cookie_pool = CookiePoolManager()


# Fonction helper pour usage externe
def get_cookie_for_request() -> Optional[str]:
    """
    Récupère un cookie disponible du pool

    Returns:
        str: Chemin vers cookies.txt ou None
    """
    return cookie_pool.get_cookie_path()


def record_request_result(cookies_path: str, success: bool, error_msg: str = None):
    """
    Enregistre le résultat d'une requête

    Args:
        cookies_path: Chemin cookies utilisé
        success: Succès ou non
        error_msg: Message d'erreur si échec
    """
    cookie_pool.record_result(cookies_path, success, error_msg)


def get_pool_statistics() -> Dict:
    """Retourne les stats du pool"""
    return cookie_pool.get_pool_stats()


if __name__ == "__main__":
    # Test du pool
    print("\n🧪 TEST DU COOKIE POOL\n")

    stats = get_pool_statistics()
    print(json.dumps(stats, indent=2))
