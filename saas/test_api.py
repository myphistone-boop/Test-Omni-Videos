"""
Script de test pour l'API YouTube to Shorts
Teste tous les endpoints
"""

import requests
import time
import sys

API_URL = "http://localhost:8000"

def test_health():
    """Test de l'endpoint health check"""
    print("🧪 Test 1: Health Check")
    print("-" * 50)

    try:
        response = requests.get(f"{API_URL}/")
        assert response.status_code == 200
        data = response.json()

        print(f"✅ Status: {data['status']}")
        print(f"✅ Service: {data['service']}")
        print(f"✅ Version: {data['version']}")
        print()
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print()
        return False


def test_process_video():
    """Test du processing d'une vidéo"""
    print("🧪 Test 2: Process Video")
    print("-" * 50)

    # Utiliser une vidéo YouTube courte pour test rapide
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    print(f"📹 URL de test: {test_url}")

    try:
        # Lancer le processing
        response = requests.post(
            f"{API_URL}/api/process",
            json={
                "video_url": test_url,
                "language": "en",
                "target_platform": "tiktok"
            }
        )

        assert response.status_code == 200
        job = response.json()

        job_id = job['job_id']
        print(f"✅ Job créé: {job_id}")
        print(f"   Status: {job['status']}")
        print(f"   Message: {job['message']}")
        print()

        # Polling du status
        print("⏳ Polling du status...")
        max_wait = 300  # 5 minutes max
        start_time = time.time()

        while time.time() - start_time < max_wait:
            response = requests.get(f"{API_URL}/api/status/{job_id}")
            status_data = response.json()

            progress = status_data['progress']
            message = status_data['message']
            status = status_data['status']

            print(f"   [{progress}%] {message}")

            if status == "completed":
                print()
                print("✅ Processing terminé !")
                print(f"   Download URL: {status_data['download_url']}")
                print()
                return True, job_id

            elif status == "failed":
                print()
                print(f"❌ Processing échoué: {status_data.get('error', 'Unknown error')}")
                print()
                return False, job_id

            time.sleep(2)

        print()
        print("⏰ Timeout - processing trop long")
        print()
        return False, job_id

    except Exception as e:
        print(f"❌ Erreur: {e}")
        print()
        return False, None


def test_download(job_id):
    """Test du téléchargement"""
    print("🧪 Test 3: Download Video")
    print("-" * 50)

    if not job_id:
        print("⏭️  Skipped (pas de job_id)")
        print()
        return False

    try:
        response = requests.get(f"{API_URL}/api/download/{job_id}")

        if response.status_code == 200:
            # Sauvegarder le fichier
            filename = f"test_output_{job_id[:8]}.mp4"
            with open(filename, 'wb') as f:
                f.write(response.content)

            print(f"✅ Vidéo téléchargée: {filename}")
            print(f"   Taille: {len(response.content) / 1024 / 1024:.2f} MB")
            print()
            return True
        else:
            print(f"❌ Erreur {response.status_code}")
            print()
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        print()
        return False


def test_list_jobs():
    """Test de la liste des jobs"""
    print("🧪 Test 4: List Jobs")
    print("-" * 50)

    try:
        response = requests.get(f"{API_URL}/api/jobs")
        assert response.status_code == 200
        data = response.json()

        jobs = data.get('jobs', [])
        print(f"✅ Nombre de jobs: {len(jobs)}")

        if jobs:
            print(f"   Dernier job:")
            last_job = jobs[-1]
            print(f"   - ID: {last_job['job_id']}")
            print(f"   - Status: {last_job['status']}")
            print(f"   - Progress: {last_job['progress']}%")

        print()
        return True

    except Exception as e:
        print(f"❌ Erreur: {e}")
        print()
        return False


def main():
    """Lance tous les tests"""
    print()
    print("=" * 50)
    print("🧪 TEST SUITE - YouTube to Shorts API")
    print("=" * 50)
    print()

    # Test 1: Health check
    if not test_health():
        print("❌ API n'est pas accessible")
        print("   Lancez d'abord: python backend/main.py")
        sys.exit(1)

    # Test 2: Process video (optionnel - prend du temps)
    print("⚠️  Le test de processing prend plusieurs minutes.")
    choice = input("Voulez-vous continuer ? (o/N): ")

    if choice.lower() == 'o':
        success, job_id = test_process_video()

        if success and job_id:
            # Test 3: Download
            test_download(job_id)

    # Test 4: List jobs
    test_list_jobs()

    print("=" * 50)
    print("✅ Tests terminés !")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
