# 🚀 YouTube to Shorts SaaS

SaaS complet pour transformer des vidéos YouTube en Shorts viraux (9:16 + sous-titres automatiques).

## ✨ Features

- ✅ **Input:** URL YouTube
- ✅ **Output:** Short téléchargeable (MP4 9:16)
- ✅ **Sous-titres automatiques** (FR/EN)
- ✅ **Effets viraux** intégrés
- ✅ **Multi-plateforme:** TikTok, YouTube Shorts, Instagram Reels
- ✅ **Processing asynchrone** avec tracking en temps réel
- ✅ **API REST** complète

---

## 📁 Structure du Projet

```
saas/
├── backend/           # API FastAPI
│   ├── main.py       # API principale
│   └── requirements.txt
├── frontend/          # Interface web
│   └── index.html    # UI simple (HTML/JS/CSS)
├── worker/            # Processing (Celery - optionnel)
└── shared/            # Code partagé
```

---

## 🚀 Quick Start (Mode Développement)

### Prérequis

- Python 3.9+
- FFmpeg installé
- Code de processing existant (`create_subtitled_video.py`, `youtube_downloader.py`)

### 1. Backend (API)

```bash
# Installer les dépendances
cd saas/backend
pip install -r requirements.txt

# Lancer le serveur API
python main.py

# API disponible sur: http://localhost:8000
# Docs interactives: http://localhost:8000/docs
```

### 2. Frontend

```bash
# Ouvrir dans un navigateur
cd saas/frontend
python -m http.server 3000

# Interface disponible sur: http://localhost:3000
```

Ou simplement ouvrir `frontend/index.html` directement dans votre navigateur.

---

## 📡 API Endpoints

### `POST /api/process`

Lance le processing d'une vidéo.

**Request:**
```json
{
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "language": "fr",
  "target_platform": "tiktok"
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "progress": 0,
  "message": "Job créé",
  "created_at": "2024-01-15T10:00:00"
}
```

### `GET /api/status/{job_id}`

Récupère le status d'un job.

**Response:**
```json
{
  "job_id": "123e4567...",
  "status": "processing",
  "progress": 65,
  "message": "Génération des sous-titres...",
  "created_at": "2024-01-15T10:00:00"
}
```

**Status possibles:**
- `pending`: En attente
- `processing`: En cours
- `completed`: Terminé
- `failed`: Erreur

### `GET /api/download/{job_id}`

Télécharge la vidéo générée (quand status = completed).

**Response:** Fichier MP4

### `DELETE /api/jobs/{job_id}`

Supprime un job et son fichier.

### `GET /api/jobs`

Liste tous les jobs (admin).

---

## 🎨 Frontend - Utilisation

1. **Ouvrir** `http://localhost:3000`
2. **Coller** une URL YouTube
3. **Sélectionner** langue et plateforme
4. **Cliquer** "Générer le Short"
5. **Attendre** le processing (barre de progression)
6. **Télécharger** le short généré

---

## 🔧 Configuration

### Variables d'environnement (`.env`)

```bash
# Backend
API_HOST=0.0.0.0
API_PORT=8000

# Storage
OUTPUT_DIR=/tmp/shorts_output

# Celery (optionnel)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Database (optionnel pour prod)
DATABASE_URL=postgresql://user:pass@localhost:5432/shorts_db
```

---

## 🐳 Docker (Production)

### Lancer avec Docker Compose

```bash
docker-compose up -d
```

**Services:**
- API Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Redis (Celery broker)
- PostgreSQL (Database)

---

## 📊 Workflow Technique

```
1. User colle URL YouTube
   ↓
2. Frontend → POST /api/process → Backend API
   ↓
3. API crée un job UUID et retourne job_id
   ↓
4. BackgroundTask (ou Celery) commence processing:
   a. Télécharge vidéo YouTube
   b. Extrait segment viral
   c. Génère sous-titres
   d. Convertit en 9:16
   e. Ajoute effets
   f. Sauvegarde dans OUTPUT_DIR
   ↓
5. Frontend poll GET /api/status/{job_id} toutes les 2s
   ↓
6. Quand status = completed, affiche bouton téléchargement
   ↓
7. User clique → GET /api/download/{job_id} → Télécharge MP4
```

---

## 🚀 Déploiement Production

### Option 1: Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Option 2: Render

1. Push code sur GitHub
2. Créer nouveau Web Service sur Render
3. Connecter le repo
4. Render détecte automatiquement FastAPI

### Option 3: Fly.io

```bash
flyctl launch
flyctl deploy
```

### Option 4: VPS (Contabo, Digital Ocean, etc.)

```bash
# Sur le serveur
git clone <repo>
cd saas/backend
pip install -r requirements.txt

# Lancer avec gunicorn (production)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Avec systemd pour auto-restart
sudo systemctl enable shorts-api
sudo systemctl start shorts-api
```

---

## 💰 Monétisation (À ajouter)

### Stripe Integration

1. Créer compte Stripe
2. Ajouter `stripe` au requirements.txt
3. Implémenter plans:
   - Free: 2 vidéos/mois
   - Pro: $29/mois (50 vidéos)
   - Business: $99/mois (illimité)

### Auth (À ajouter)

- Clerk.com (le plus simple)
- Supabase Auth
- Auth0

---

## 📈 Scaling

Pour gérer plus de 100 jobs/jour:

1. **Celery + Redis** pour queue distribuée
2. **PostgreSQL** pour database persistente
3. **AWS S3** ou **Cloudflare R2** pour stockage vidéos
4. **Load balancer** (Nginx) devant plusieurs workers
5. **CDN** pour servir les vidéos

---

## 🐛 Troubleshooting

### Backend ne démarre pas
```bash
# Vérifier Python version
python --version  # Doit être 3.9+

# Réinstaller dépendances
pip install -r requirements.txt --force-reinstall
```

### Processing échoue
```bash
# Vérifier FFmpeg
ffmpeg -version

# Vérifier permissions OUTPUT_DIR
ls -la /tmp/shorts_output
```

### CORS errors
```bash
# Modifier dans main.py:
allow_origins=["http://localhost:3000"]  # Ajouter votre domaine
```

---

## 📝 TODO / Améliorations

- [ ] Ajouter Celery pour queue distribuée
- [ ] Implémenter PostgreSQL (remplacer jobs_db dict)
- [ ] Ajouter authentification (Clerk/Supabase)
- [ ] Intégrer Stripe pour paiements
- [ ] Ajouter upload de fichier (en plus de URL)
- [ ] WebSocket pour real-time progress
- [ ] Dashboard admin (stats, monitoring)
- [ ] Rate limiting API
- [ ] Watermark optionnel
- [ ] Templates de styles (différents effets)
- [ ] Batch processing (plusieurs URLs à la fois)
- [ ] Scheduler pour processing différé
- [ ] Intégration TikTok/Instagram API (auto-upload)

---

## 📞 Support

Pour questions/bugs:
- GitHub Issues
- Email: support@example.com

---

## ⚖️ Disclaimer

Cette application est fournie "as is" à des fins éducatives.
Les utilisateurs sont responsables de respecter les droits d'auteur
et les conditions d'utilisation des plateformes tierces.

---

## 🎉 Prêt à lancer !

```bash
# Terminal 1: Backend
cd saas/backend && python main.py

# Terminal 2: Frontend
cd saas/frontend && python -m http.server 3000

# Ouvrir http://localhost:3000
```

**Enjoy! 🚀**
