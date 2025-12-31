"""
FastAPI Backend - YouTube to Shorts SaaS
API principale pour accepter URLs et gérer les jobs de processing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import os

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
    cookies_file: Optional[UploadFile] = File(None)
):
    """
    Lance le processing d'une vidéo YouTube

    Args:
        video_url: URL YouTube
        language: Langue (fr/en)
        target_platform: Plateforme cible
        cookies_file: Fichier cookies.txt (optionnel)

    Returns:
        JobStatus avec job_id pour tracking
    """

    # Créer un job unique
    job_id = str(uuid.uuid4())

    # Sauvegarder les cookies si fournis
    cookies_path = None
    if cookies_file:
        cookies_path = OUTPUT_DIR / f"{job_id}_cookies.txt"
        with open(cookies_path, "wb") as f:
            content = await cookies_file.read()
            f.write(content)

    # Initialiser le job
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Job créé, en attente de processing",
        "created_at": datetime.now(),
        "video_url": video_url,
        "language": language,
        "target_platform": target_platform,
        "cookies_path": str(cookies_path) if cookies_path else None
    }

    # Lancer le processing en background
    background_tasks.add_task(
        process_video_task,
        job_id,
        video_url,
        language,
        target_platform
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


# ==========================================
# WORKER FUNCTION (à déplacer vers Celery)
# ==========================================

def process_video_task(job_id: str, video_url: str, language: str, target_platform: str):
    """
    Traite une vidéo YouTube en short

    Cette fonction sera remplacée par une tâche Celery en production
    Pour l'instant elle tourne en background task FastAPI
    """

    try:
        # Update status: en cours
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 10
        jobs_db[job_id]["message"] = "Téléchargement de la vidéo..."

        # Import des modules de processing
        from youtube_downloader import download_video

        jobs_db[job_id]["progress"] = 30
        jobs_db[job_id]["message"] = "Extraction du segment viral..."

        # Récupérer le chemin des cookies si fourni
        cookies_path = jobs_db[job_id].get("cookies_path")

        # Télécharger la vidéo
        temp_video = str(Path(tempfile.gettempdir()) / f"{job_id}_original.mp4")
        download_video(video_url, temp_video, cookies_path=cookies_path)

        jobs_db[job_id]["progress"] = 50
        jobs_db[job_id]["message"] = "Génération des sous-titres..."

        # Importer et utiliser le video processor
        from video_processor import create_short_video

        output_path = OUTPUT_DIR / f"{job_id}.mp4"

        jobs_db[job_id]["progress"] = 70
        jobs_db[job_id]["message"] = "Création du short (9:16 + effets)..."

        # Créer le short
        create_short_video(
            input_video=temp_video,
            output_path=str(output_path),
            language=language
        )

        jobs_db[job_id]["progress"] = 90
        jobs_db[job_id]["message"] = "Finalisation..."

        # Nettoyer les fichiers temporaires
        if os.path.exists(temp_video):
            os.remove(temp_video)

        # Nettoyer le fichier cookies
        if cookies_path and os.path.exists(cookies_path):
            os.remove(cookies_path)

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
