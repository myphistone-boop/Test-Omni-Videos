# 🚀 Guide de Déploiement - YouTube to Shorts SaaS

Guide complet pour déployer votre SaaS en production.

---

## 📋 Checklist Pré-Déploiement

- [ ] FFmpeg installé sur le serveur
- [ ] Python 3.9+ installé
- [ ] Domaine configuré (ex: shorts.example.com)
- [ ] SSL/HTTPS configuré
- [ ] Variables d'environnement configurées
- [ ] Base de données setup (PostgreSQL recommandé)
- [ ] Storage configuré (S3, R2, ou local)
- [ ] Monitoring configuré (Sentry, etc.)

---

## 🎯 Options de Déploiement

### Option 1: Railway.app (Le Plus Simple) ⭐ RECOMMANDÉ

**Avantages:**
- ✅ Déploiement en 5 minutes
- ✅ PostgreSQL inclus gratuitement
- ✅ SSL automatique
- ✅ Scaling automatique
- ✅ $5/mois pour commencer

**Steps:**

```bash
# 1. Installer Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Créer nouveau projet
cd saas
railway init

# 4. Ajouter PostgreSQL
railway add

# 5. Deploy
railway up

# 6. Obtenir URL
railway domain
```

**Variables d'env à configurer:**
- `PYTHON_VERSION=3.11`
- `OUTPUT_DIR=/app/output`

---

### Option 2: Render.com

**Avantages:**
- ✅ Free tier disponible
- ✅ PostgreSQL gratuit
- ✅ Facile à configurer
- ✅ Auto-deploy depuis GitHub

**Steps:**

1. Push code sur GitHub
2. Aller sur render.com
3. New → Web Service
4. Connecter GitHub repo
5. Configurer:
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3.11

---

### Option 3: Fly.io

**Avantages:**
- ✅ Très performant
- ✅ Edge locations
- ✅ Scaling facile

**Steps:**

```bash
# 1. Installer Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Launch app
cd saas
flyctl launch

# 4. Deploy
flyctl deploy
```

---

### Option 4: VPS (Digital Ocean, Contabo, etc.)

**Avantages:**
- ✅ Contrôle total
- ✅ Moins cher long terme
- ✅ Ressources dédiées

**Steps:**

#### 1. Setup Serveur

```bash
# SSH dans le serveur
ssh root@your-server-ip

# Update système
apt update && apt upgrade -y

# Installer dépendances
apt install -y python3.11 python3-pip ffmpeg nginx certbot python3-certbot-nginx git redis-server postgresql

# Créer user
adduser shorts
usermod -aG sudo shorts
su - shorts
```

#### 2. Clone & Setup

```bash
# Clone repo
git clone <votre-repo> ~/saas
cd ~/saas

# Setup venv
python3 -m venv venv
source venv/bin/activate

# Install deps
cd backend
pip install -r requirements.txt
pip install gunicorn

# Setup PostgreSQL
sudo -u postgres createuser shorts
sudo -u postgres createdb shorts_db
sudo -u postgres psql -c "ALTER USER shorts WITH PASSWORD 'votre-password';"
```

#### 3. Setup Systemd (auto-restart)

```bash
sudo nano /etc/systemd/system/shorts-api.service
```

```ini
[Unit]
Description=Shorts API
After=network.target

[Service]
User=shorts
WorkingDirectory=/home/shorts/saas/backend
Environment="PATH=/home/shorts/saas/venv/bin"
ExecStart=/home/shorts/saas/venv/bin/gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

> ⚠️ **Important**: Utilisez `-w 1` (1 worker) car l'application utilise un stockage en mémoire pour les jobs.
> Avec plusieurs workers, les jobs créés par un worker ne sont pas accessibles aux autres workers.
>
> **Solutions pour multi-workers:**
> - Implémenter Redis pour partager l'état entre workers
> - Ou utiliser PostgreSQL pour stocker les jobs
> - Pour un MVP, 1 worker est suffisant pour ~10-20 utilisateurs simultanés

```bash
# Enable & start
sudo systemctl enable shorts-api
sudo systemctl start shorts-api
sudo systemctl status shorts-api
```

#### 4. Setup Nginx

```bash
sudo nano /etc/nginx/sites-available/shorts
```

```nginx
server {
    listen 80;
    server_name shorts.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    client_max_body_size 500M;  # Pour uploads
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/shorts /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL
sudo certbot --nginx -d shorts.example.com
```

---

## 🔐 Sécurité

### 1. Variables d'environnement

**NE JAMAIS commit:**
- `client_secrets.json`
- `.env` avec clés API
- Credentials PostgreSQL

**Utiliser:**
- `.env.example` dans repo
- Secrets manager du provider (Railway Secrets, Render Env Vars, etc.)

### 2. Rate Limiting

```python
# Ajouter dans main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/process")
@limiter.limit("5/minute")  # 5 requêtes par minute
async def process_video(...):
    ...
```

### 3. CORS

```python
# Modifier dans main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourfrontend.com",
        "https://www.yourfrontend.com"
    ],  # Pas de "*" en production !
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

---

## 💾 Database Migration (Dict → PostgreSQL)

### 1. Installer SQLAlchemy

```bash
pip install sqlalchemy psycopg2-binary alembic
```

### 2. Créer models

```python
# backend/models.py
from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True)
    status = Column(String)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    message = Column(String)
    video_url = Column(String)
    language = Column(String)
    target_platform = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    download_url = Column(String, nullable=True)
    error = Column(String, nullable=True)
```

### 3. Modifier main.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Job
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shorts:password@localhost/shorts_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Créer tables
Base.metadata.create_all(engine)

# Remplacer jobs_db dict par DB queries
@app.post("/api/process")
async def process_video(request: VideoRequest):
    db = SessionLocal()

    job = Job(
        job_id=str(uuid.uuid4()),
        status="pending",
        video_url=str(request.video_url),
        language=request.language,
        target_platform=request.target_platform
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job
```

---

## 📊 Monitoring

### Sentry (Erreurs)

```bash
pip install sentry-sdk[fastapi]
```

```python
# main.py
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxx@xxx.ingest.sentry.io/xxx",
    traces_sample_rate=1.0,
)
```

### Logs

```bash
# Voir logs en temps réel
railway logs  # Railway
render logs   # Render
flyctl logs   # Fly.io
journalctl -u shorts-api -f  # VPS
```

---

## 📈 Scaling

### Horizontal Scaling

**Railway / Render:**
- Augmenter nombre de replicas dans dashboard
- Auto-scaling disponible sur plans supérieurs

**VPS:**
- Load balancer (Nginx) devant plusieurs workers
- PM2 pour gérer plusieurs processes:

```bash
npm install -g pm2

pm2 start "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000" --name shorts-api
pm2 save
pm2 startup
```

### Celery Workers (Pour heavy processing)

```bash
# Sur serveur séparé ou container
celery -A worker worker --loglevel=info --concurrency=4
```

---

## 💰 Coûts Estimés

### MVP (0-100 users/jour)

| Service | Provider | Coût/mois |
|---------|----------|-----------|
| API Hosting | Railway | $5 |
| Database | Railway (inclus) | $0 |
| Storage (50GB) | Cloudflare R2 | $1 |
| **TOTAL** | | **~$6/mois** |

### Scale (1000 users/jour)

| Service | Provider | Coût/mois |
|---------|----------|-----------|
| API Hosting | Railway | $20 |
| Workers | Railway | $20 |
| Database | Railway | $10 |
| Storage (500GB) | Cloudflare R2 | $8 |
| CDN | Cloudflare | $0 (gratuit) |
| **TOTAL** | | **~$58/mois** |

### Enterprise (10K+ users/jour)

| Service | Provider | Coût/mois |
|---------|----------|-----------|
| Load Balancer | Digital Ocean | $12 |
| API Servers (3x) | Digital Ocean | $72 |
| Workers (2x) | Digital Ocean | $48 |
| Database | Managed PostgreSQL | $35 |
| Redis | Managed Redis | $15 |
| Storage (5TB) | S3 | $115 |
| CDN | CloudFront | $50 |
| **TOTAL** | | **~$347/mois** |

---

## 🧪 Testing Production

```bash
# Test API
curl https://shorts.example.com/

# Test process
curl -X POST https://shorts.example.com/api/process \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtube.com/watch?v=...", "language": "fr"}'
```

---

## 🔄 CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: |
          npm i -g @railway/cli
          railway link ${{ secrets.RAILWAY_PROJECT_ID }}
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

---

## ✅ Go Live Checklist

- [ ] Domain acheté et configuré
- [ ] SSL/HTTPS actif
- [ ] Database backup configuré
- [ ] Monitoring actif (Sentry)
- [ ] Rate limiting activé
- [ ] CORS configuré correctement
- [ ] Variables d'env sécurisées
- [ ] Health checks configurés
- [ ] Logs accessibles
- [ ] Plan de scaling défini
- [ ] Support/Contact configuré
- [ ] Legal pages (Terms, Privacy) ajoutées
- [ ] Analytics configuré (Google Analytics, Plausible)

**Prêt à lancer! 🚀**
