# 🚀 Déploiement SaaS YouTube to Shorts sur Contabo VPS

Guide complet pour déployer votre SaaS sur un VPS Contabo.

---

## 📋 Prérequis

- ✅ VPS Contabo actif
- ✅ Accès root (IP + password)
- ✅ Domaine acheté (optionnel mais recommandé)
- ✅ Code SaaS sur GitHub

---

## 🔧 Étape 1: Connexion au VPS

### Depuis Windows (PowerShell):

```powershell
# SSH vers votre VPS
ssh root@VOTRE_IP_CONTABO

# Exemple:
# ssh root@123.45.67.89
```

**Première connexion:**
- Tapez "yes" quand demandé
- Entrez le mot de passe root fourni par Contabo
- Changez le mot de passe si demandé

---

## 🛠️ Étape 2: Setup Initial du Serveur

```bash
# Update système
apt update && apt upgrade -y

# Installer les dépendances
apt install -y python3.11 python3-pip python3-venv \
    ffmpeg nginx certbot python3-certbot-nginx \
    git redis-server postgresql postgresql-contrib \
    ufw htop curl wget

# Vérifier les versions
python3 --version  # Doit être 3.11+
ffmpeg -version
nginx -v
```

---

## 👤 Étape 3: Créer un User (Sécurité)

**Ne PAS tout faire en root !**

```bash
# Créer user 'shorts'
adduser shorts
# Entrez un mot de passe quand demandé

# Donner privilèges sudo
usermod -aG sudo shorts

# Passer sur ce user
su - shorts
```

---

## 📥 Étape 4: Cloner le Code

```bash
# Se placer dans home
cd ~

# Cloner votre repo
git clone https://github.com/VOTRE_USERNAME/Test-Omni-Videos.git
# Ou si privé, utilisez token GitHub

cd Test-Omni-Videos
```

---

## 🗄️ Étape 5: Setup PostgreSQL

```bash
# Passer en user postgres temporairement
sudo -u postgres psql

# Dans psql:
CREATE USER shorts WITH PASSWORD 'VOTRE_MOT_DE_PASSE_SECURE';
CREATE DATABASE shorts_db OWNER shorts;
GRANT ALL PRIVILEGES ON DATABASE shorts_db TO shorts;
\q

# Tester la connexion
psql -U shorts -d shorts_db -h localhost
# Mot de passe demandé, puis \q pour sortir
```

---

## 🐍 Étape 6: Setup Python Environment

```bash
cd ~/Test-Omni-Videos/saas/backend

# Créer venv
python3 -m venv venv

# Activer
source venv/bin/activate

# Installer dépendances
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Pour production

# Copier fichiers de processing
cp ../../create_subtitled_video.py .
cp ../../youtube_downloader.py .
cp ../../discover_viral_videos.py .
```

---

## ⚙️ Étape 7: Configuration Environnement

```bash
# Créer fichier .env
cd ~/Test-Omni-Videos/saas/backend
nano .env
```

**Contenu du .env:**
```bash
API_HOST=0.0.0.0
API_PORT=8000
OUTPUT_DIR=/home/shorts/videos_output
DATABASE_URL=postgresql://shorts:VOTRE_MOT_DE_PASSE@localhost/shorts_db
REDIS_URL=redis://localhost:6379/0
```

Sauvegarder: `Ctrl+O` puis `Enter`, Quitter: `Ctrl+X`

```bash
# Créer dossier output
mkdir -p /home/shorts/videos_output
```

---

## 🔧 Étape 8: Setup Systemd (Auto-restart)

```bash
sudo nano /etc/systemd/system/shorts-api.service
```

**Contenu:**
```ini
[Unit]
Description=YouTube to Shorts API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=shorts
WorkingDirectory=/home/shorts/Test-Omni-Videos/saas/backend
Environment="PATH=/home/shorts/Test-Omni-Videos/saas/backend/venv/bin"
EnvironmentFile=/home/shorts/Test-Omni-Videos/saas/backend/.env
ExecStart=/home/shorts/Test-Omni-Videos/saas/backend/venv/bin/gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile /home/shorts/api.log \
    --error-logfile /home/shorts/api-error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Sauvegarder et quitter.

```bash
# Enable et start le service
sudo systemctl daemon-reload
sudo systemctl enable shorts-api
sudo systemctl start shorts-api

# Vérifier le status
sudo systemctl status shorts-api

# Voir les logs
sudo journalctl -u shorts-api -f
```

**Vous devriez voir:**
```
● shorts-api.service - YouTube to Shorts API
   Active: active (running)
```

---

## 🌐 Étape 9: Setup Nginx (Reverse Proxy)

```bash
sudo nano /etc/nginx/sites-available/shorts
```

**Contenu:**
```nginx
# Sans domaine (utiliser IP directement)
server {
    listen 80;
    server_name VOTRE_IP_CONTABO;  # Ex: 123.45.67.89

    client_max_body_size 500M;

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }

    # Docs API
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }

    # Health check
    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Frontend (à ajouter plus tard)
    # location / {
    #     root /home/shorts/Test-Omni-Videos/saas/frontend;
    #     try_files $uri $uri/ /index.html;
    # }
}
```

**Si vous avez un domaine (ex: shorts.example.com):**
```nginx
server {
    listen 80;
    server_name shorts.example.com;  # Votre domaine

    # ... reste identique
}
```

Sauvegarder et quitter.

```bash
# Enable le site
sudo ln -s /etc/nginx/sites-available/shorts /etc/nginx/sites-enabled/

# Tester la config
sudo nginx -t

# Si OK, recharger Nginx
sudo systemctl reload nginx
```

---

## 🔒 Étape 10: Firewall (Sécurité)

```bash
# Setup UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable
sudo ufw enable

# Vérifier
sudo ufw status
```

**Résultat attendu:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## 🔐 Étape 11: SSL (HTTPS) - Si vous avez un domaine

**Avant:** Assurez-vous que votre domaine pointe vers l'IP Contabo (DNS A record)

```bash
# Installer certificat SSL automatique
sudo certbot --nginx -d shorts.example.com

# Suivez les instructions:
# - Entrez votre email
# - Acceptez les ToS
# - Choisissez "2" pour rediriger HTTP vers HTTPS

# Auto-renewal (déjà configuré, vérifier):
sudo systemctl status certbot.timer
```

**Sans domaine:** Vous utilisez juste HTTP avec l'IP (http://VOTRE_IP)

---

## ✅ Étape 12: Test du Déploiement

### Test 1: API Health Check

```bash
# Depuis le VPS
curl http://localhost:8000/

# Depuis votre PC
# http://VOTRE_IP_CONTABO/
```

**Résultat attendu:**
```json
{
  "status": "online",
  "service": "YouTube to Shorts API",
  "version": "1.0.0"
}
```

### Test 2: Docs API

Ouvrir dans le navigateur:
```
http://VOTRE_IP_CONTABO/docs
```

Vous devriez voir l'interface Swagger !

### Test 3: Test Processing

```bash
# Depuis le VPS
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "en",
    "target_platform": "tiktok"
  }'
```

---

## 📊 Monitoring et Maintenance

### Voir les logs en temps réel:

```bash
# Logs API
sudo journalctl -u shorts-api -f

# Logs Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs API personnalisés
tail -f ~/api.log
tail -f ~/api-error.log
```

### Redémarrer les services:

```bash
# Redémarrer API
sudo systemctl restart shorts-api

# Redémarrer Nginx
sudo systemctl restart nginx

# Voir le statut
sudo systemctl status shorts-api
```

### Mettre à jour le code:

```bash
cd ~/Test-Omni-Videos
git pull origin claude/viral-video-automation-rVrxL

# Redémarrer l'API
sudo systemctl restart shorts-api
```

---

## 🎨 Étape 13: Déployer le Frontend

### Option A: Servir avec Nginx (Recommandé)

```bash
# Modifier config Nginx
sudo nano /etc/nginx/sites-available/shorts
```

Ajouter/décommenter la section frontend:
```nginx
# Frontend
location / {
    root /home/shorts/Test-Omni-Videos/saas/frontend;
    try_files $uri $uri/ /index.html;
    index index.html;
}
```

**Modifier le frontend pour pointer vers l'API:**
```bash
nano ~/Test-Omni-Videos/saas/frontend/index.html
```

Changer la ligne (vers ligne 179):
```javascript
// De:
const API_URL = 'http://localhost:8000';

// À:
const API_URL = window.location.origin;  // Utilise le même domaine
// Ou si IP différente:
const API_URL = 'http://VOTRE_IP_CONTABO';
```

```bash
# Recharger Nginx
sudo systemctl reload nginx
```

**Tester:** http://VOTRE_IP_CONTABO/

---

## 🔍 Troubleshooting

### API ne démarre pas:

```bash
# Vérifier les logs
sudo journalctl -u shorts-api -n 50

# Tester manuellement
cd ~/Test-Omni-Videos/saas/backend
source venv/bin/activate
python main.py
```

### Nginx erreur 502 Bad Gateway:

```bash
# Vérifier que l'API tourne
sudo systemctl status shorts-api

# Vérifier le port
sudo netstat -tulpn | grep 8000
```

### Permissions fichiers:

```bash
# Fixer les permissions
sudo chown -R shorts:shorts /home/shorts/Test-Omni-Videos
sudo chown -R shorts:shorts /home/shorts/videos_output
```

### Database connection erreur:

```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Tester connexion
psql -U shorts -d shorts_db -h localhost
```

---

## 📈 Optimisation Production

### 1. Monitoring (Optionnel)

```bash
# Installer htop
sudo apt install htop

# Voir ressources en temps réel
htop
```

### 2. Log Rotation

```bash
sudo nano /etc/logrotate.d/shorts-api
```

```
/home/shorts/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 0644 shorts shorts
}
```

### 3. Backup automatique

```bash
# Script de backup
nano ~/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/shorts/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Database
pg_dump -U shorts shorts_db > $BACKUP_DIR/db_$DATE.sql

# Backup vidéos (si stockage local)
tar -czf $BACKUP_DIR/videos_$DATE.tar.gz /home/shorts/videos_output

# Garder seulement 7 derniers backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x ~/backup.sh

# Ajouter au cron (backup quotidien à 3h du matin)
crontab -e
```

Ajouter:
```
0 3 * * * /home/shorts/backup.sh >> /home/shorts/backup.log 2>&1
```

---

## ✅ Checklist Finale

- [ ] VPS accessible via SSH
- [ ] Système à jour (apt update/upgrade)
- [ ] User 'shorts' créé
- [ ] PostgreSQL configuré
- [ ] Redis installé
- [ ] Code cloné depuis GitHub
- [ ] Python venv créé et deps installées
- [ ] Service systemd configuré et actif
- [ ] Nginx configuré et actif
- [ ] Firewall (UFW) activé
- [ ] SSL installé (si domaine)
- [ ] API accessible (http://VOTRE_IP/docs)
- [ ] Frontend accessible
- [ ] Test de processing réussi

---

## 🎉 Vous êtes en production !

**Votre SaaS est maintenant accessible à:**
- **Sans domaine:** http://VOTRE_IP_CONTABO
- **Avec domaine:** https://shorts.example.com

**Coût total:** ~6-15€/mois (juste le VPS Contabo)

---

## 🚀 Prochaines Étapes

1. **Tester** avec vraies vidéos
2. **Customiser** le frontend (logo, couleurs)
3. **Ajouter** Stripe pour monétisation
4. **Marketing** - Partager sur réseaux sociaux
5. **Scaler** quand vous avez 100+ users

**Enjoy! 🎉**
