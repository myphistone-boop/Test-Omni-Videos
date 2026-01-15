"""
FastAPI Backend - YouTube to Shorts SaaS
API principale pour accepter URLs et gérer les jobs de processing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import os
import secrets

# Import worker tasks
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

app = FastAPI(
    title="YouTube to Shorts API",
    description="Transform YouTube videos into TikTok/YouTube Shorts",
    version="1.0.0"
)

# CORS pour frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de données simple (à remplacer par PostgreSQL en prod)
jobs_db = {}

# Output directory - compatible Windows/Linux
import tempfile
OUTPUT_DIR = Path(tempfile.gettempdir()) / "shorts_output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


class VideoRequest(BaseModel):
    """Request pour traiter une vidéo"""
    video_url: HttpUrl
    language: str = "fr"  # fr ou en
    target_platform: str = "tiktok"  # tiktok, youtube_shorts, instagram


class JobStatus(BaseModel):
    """Status d'un job de processing"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "YouTube to Shorts API",
        "version": "1.0.0"
    }


@app.post("/api/process", response_model=JobStatus)
async def process_video(
    background_tasks: BackgroundTasks,
    video_url: str = Form(...),
    language: str = Form("fr"),
    target_platform: str = Form("tiktok"),
    transcription_mode: str = Form("youtube_subs")  # 'youtube_subs' ou 'whisper'
):
    """
    Lance le processing d'une vidéo YouTube (mode public, sans cookies)

    Args:
        video_url: URL YouTube
        language: Langue (fr/en)
        target_platform: Plateforme cible
        transcription_mode: Mode de transcription ('youtube_subs' ou 'whisper')

    Returns:
        JobStatus avec job_id pour tracking

    Note:
        Fonctionne SANS cookies pour les vidéos publiques YouTube (60-80% des cas).
        Si échec, le message d'erreur indiquera comment procéder.
    """

    # Créer un job unique
    job_id = str(uuid.uuid4())

    # Initialiser le job (plus besoin de cookies_path)
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Job créé, en attente de processing (mode public)",
        "created_at": datetime.now(),
        "video_url": video_url,
        "language": language,
        "target_platform": target_platform,
        "transcription_mode": transcription_mode
    }

    # Lancer le processing en background
    background_tasks.add_task(
        process_video_task,
        job_id,
        video_url,
        language,
        target_platform,
        transcription_mode
    )

    return JobStatus(**jobs_db[job_id])


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Récupère le status d'un job

    Args:
        job_id: ID du job à vérifier

    Returns:
        JobStatus avec progression actuelle
    """

    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job introuvable")

    return JobStatus(**jobs_db[job_id])


@app.get("/api/download/{job_id}")
async def download_video(job_id: str):
    """
    Télécharge la vidéo générée

    Args:
        job_id: ID du job

    Returns:
        Fichier vidéo MP4
    """

    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job introuvable")

    job = jobs_db[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job pas encore terminé (status: {job['status']})"
        )

    # Chemin du fichier généré
    video_path = OUTPUT_DIR / f"{job_id}.mp4"

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"short_{job_id}.mp4"
    )


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Supprime un job et son fichier

    Args:
        job_id: ID du job à supprimer
    """

    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job introuvable")

    # Supprimer le fichier si existe
    video_path = OUTPUT_DIR / f"{job_id}.mp4"
    if video_path.exists():
        video_path.unlink()

    # Supprimer le job de la DB
    del jobs_db[job_id]

    return {"message": "Job supprimé"}


@app.get("/api/jobs")
async def list_jobs():
    """Liste tous les jobs (pour admin)"""
    return {"jobs": list(jobs_db.values())}


@app.get("/api/cookie-status")
async def get_cookie_status():
    """
    Récupère le statut du cookie YouTube serveur

    Returns:
        {
            "status": "ok" | "invalid" | "warning" | "missing",
            "message": "Cookie valide",
            "last_check": "2026-01-14T10:30:00",
            "last_success": "2026-01-14T10:30:00",
            "age_hours": 2.5,
            "health_score": 100
        }
    """
    try:
        from cookie_monitor import CookieStatus
        monitor = CookieStatus()
        return monitor.get_status()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors de la récupération du statut: {str(e)}",
            "health_score": 0
        }


@app.post("/api/upload-cookie")
async def upload_cookie(cookie_file: UploadFile = File(...)):
    """
    Upload un nouveau fichier de cookies YouTube

    Args:
        cookie_file: Fichier cookies.txt au format Netscape

    Returns:
        {
            "success": True,
            "message": "Cookie uploadé avec succès"
        }
    """
    try:
        from cookie_monitor import CookieStatus, COOKIE_DIR, COOKIE_FILE

        # Vérifier que c'est un fichier .txt
        if not cookie_file.filename.endswith('.txt'):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être au format .txt"
            )

        # Créer le dossier si nécessaire
        COOKIE_DIR.mkdir(parents=True, exist_ok=True)

        # Lire le contenu
        content = await cookie_file.read()

        # Valider que c'est bien un fichier cookie Netscape
        content_str = content.decode('utf-8')
        if '# Netscape HTTP Cookie File' not in content_str and 'youtube.com' not in content_str:
            raise HTTPException(
                status_code=400,
                detail="Le fichier ne semble pas être un fichier de cookies YouTube valide"
            )

        # Sauvegarder le fichier
        with open(COOKIE_FILE, 'wb') as f:
            f.write(content)

        # Mettre à jour le statut
        monitor = CookieStatus()
        monitor.mark_cookie_created()

        return {
            "success": True,
            "message": "Cookie uploadé avec succès et marqué comme actif"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'upload: {str(e)}"
        )


# ==========================================
# WORKER FUNCTION (à déplacer vers Celery)
# ==========================================

def process_video_task(job_id: str, video_url: str, language: str, target_platform: str, transcription_mode: str = "youtube_subs"):
    """
    Traite une vidéo YouTube en short (mode public, sans cookies)

    Cette fonction sera remplacée par une tâche Celery en production
    Pour l'instant elle tourne en background task FastAPI

    Args:
        job_id: ID du job
        video_url: URL YouTube
        language: Langue (fr/en)
        target_platform: Plateforme cible
        transcription_mode: Mode de transcription ('youtube_subs' ou 'whisper')
    """

    try:
        # Update status: en cours
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 10
        jobs_db[job_id]["message"] = "Téléchargement de la vidéo (mode public)..."

        # Import des modules de processing
        from youtube_downloader import download_video

        jobs_db[job_id]["progress"] = 30
        jobs_db[job_id]["message"] = "Extraction du segment viral..."

        # Télécharger la vidéo (mode public, sans cookies)
        temp_video = str(Path(tempfile.gettempdir()) / f"{job_id}_original.mp4")
        download_video(video_url, temp_video, cookies_path=None)  # None = mode public

        jobs_db[job_id]["progress"] = 50
        jobs_db[job_id]["message"] = "Génération des sous-titres..."

        # Importer le video processor RAPIDE (pipeline optimisé)
        from video_processor_fast import create_short_video_fast

        output_path = OUTPUT_DIR / f"{job_id}.mp4"

        # Créer une fonction callback pour les mises à jour de progression
        def update_progress(progress: int, message: str):
            """Callback pour mettre à jour la progression en temps réel"""
            jobs_db[job_id]["progress"] = progress
            jobs_db[job_id]["message"] = message

        # Créer le short avec pipeline rapide (mode public)
        create_short_video_fast(
            input_video=temp_video,
            output_path=str(output_path),
            language=language,
            progress_callback=update_progress,
            youtube_url=video_url,
            transcription_mode=transcription_mode,
            cookies_path=None  # None = mode public, sans cookies
        )

        # Nettoyer les fichiers temporaires
        if os.path.exists(temp_video):
            os.remove(temp_video)

        # Succès
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["message"] = "Short généré avec succès !"
        jobs_db[job_id]["completed_at"] = datetime.now()
        jobs_db[job_id]["download_url"] = f"/api/download/{job_id}"

    except Exception as e:
        # Erreur
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["progress"] = 0
        jobs_db[job_id]["message"] = "Erreur lors du processing"
        jobs_db[job_id]["error"] = str(e)
        jobs_db[job_id]["completed_at"] = datetime.now()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
