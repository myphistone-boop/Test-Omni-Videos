#!/bin/bash

###############################################################################
# 🚀 Script d'installation automatique - YouTube to Shorts SaaS
# Pour VPS Contabo (Ubuntu 22.04/24.04)
###############################################################################

set -e  # Arrêter en cas d'erreur

echo "======================================================================"
echo "🚀 Installation YouTube to Shorts SaaS sur Contabo VPS"
echo "======================================================================"
echo ""

# Couleurs pour output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier qu'on est root
if [ "$EUID" -ne 0 ]; then
    log_error "Ce script doit être exécuté en tant que root"
    log_info "Utilisez: sudo bash setup_contabo.sh"
    exit 1
fi

echo ""
log_info "Ce script va installer:"
echo "  • Python 3.11 + dépendances"
echo "  • FFmpeg (traitement vidéo)"
echo "  • PostgreSQL (database)"
echo "  • Redis (cache)"
echo "  • Nginx (web server)"
echo "  • Certbot (SSL)"
echo "  • Configuration complète du SaaS"
echo ""

# Demander confirmation
read -p "Voulez-vous continuer? (o/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    log_info "Installation annulée"
    exit 1
fi

###############################################################################
# 1. UPDATE SYSTÈME
###############################################################################

echo ""
echo "======================================================================"
echo "📦 Étape 1/10: Mise à jour du système"
echo "======================================================================"

apt update
apt upgrade -y
log_success "Système à jour"

###############################################################################
# 2. INSTALLATION DÉPENDANCES
###############################################################################

echo ""
echo "======================================================================"
echo "📦 Étape 2/10: Installation des dépendances"
echo "======================================================================"

apt install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    ffmpeg \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    redis-server \
    postgresql \
    postgresql-contrib \
    ufw \
    htop \
    curl \
    wget \
    build-essential

log_success "Dépendances installées"

###############################################################################
# 3. CRÉER USER 'shorts'
###############################################################################

echo ""
echo "======================================================================"
echo "👤 Étape 3/10: Création utilisateur 'shorts'"
echo "======================================================================"

# Vérifier si l'utilisateur existe déjà
if id "shorts" &>/dev/null; then
    log_info "L'utilisateur 'shorts' existe déjà"
else
    # Créer user sans interaction
    useradd -m -s /bin/bash shorts

    # Définir un mot de passe
    echo "shorts:ShortsPass2024!" | chpasswd

    # Ajouter aux sudoers
    usermod -aG sudo shorts

    log_success "Utilisateur 'shorts' créé (password: ShortsPass2024!)"
    log_info "Changez ce mot de passe après l'installation!"
fi

###############################################################################
# 4. SETUP POSTGRESQL
###############################################################################

echo ""
echo "======================================================================"
echo "🗄️  Étape 4/10: Configuration PostgreSQL"
echo "======================================================================"

# Démarrer PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Créer database et user
sudo -u postgres psql -c "CREATE USER shorts WITH PASSWORD 'ShortsDBPass2024!';" 2>/dev/null || log_info "User postgres 'shorts' existe déjà"
sudo -u postgres psql -c "CREATE DATABASE shorts_db OWNER shorts;" 2>/dev/null || log_info "Database 'shorts_db' existe déjà"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shorts_db TO shorts;"

log_success "PostgreSQL configuré"

###############################################################################
# 5. SETUP REDIS
###############################################################################

echo ""
echo "======================================================================"
echo "📮 Étape 5/10: Configuration Redis"
echo "======================================================================"

systemctl start redis-server
systemctl enable redis-server

log_success "Redis configuré"

###############################################################################
# 6. CLONE CODE
###############################################################################

echo ""
echo "======================================================================"
echo "📥 Étape 6/10: Récupération du code"
echo "======================================================================"

# Se placer dans le home de shorts
cd /home/shorts

# Demander l'URL du repo
echo ""
log_info "URL de votre repo GitHub"
log_info "Format: https://github.com/USERNAME/REPO.git"
echo ""
read -p "URL du repo: " REPO_URL

if [ -z "$REPO_URL" ]; then
    log_error "URL du repo requise"
    exit 1
fi

# Cloner
if [ -d "Test-Omni-Videos" ]; then
    log_info "Dossier existe déjà, pull des changements..."
    cd Test-Omni-Videos
    sudo -u shorts git pull
else
    log_info "Clonage du repo..."
    sudo -u shorts git clone "$REPO_URL" Test-Omni-Videos
fi

log_success "Code récupéré"

###############################################################################
# 7. SETUP PYTHON VENV
###############################################################################

echo ""
echo "======================================================================"
echo "🐍 Étape 7/10: Configuration Python"
echo "======================================================================"

cd /home/shorts/Test-Omni-Videos/saas/backend

# Créer venv en tant que user shorts
sudo -u shorts python3 -m venv venv

# Installer dépendances
sudo -u shorts venv/bin/pip install --upgrade pip
sudo -u shorts venv/bin/pip install -r requirements.txt
sudo -u shorts venv/bin/pip install gunicorn

# Copier fichiers de processing
sudo -u shorts cp ../../create_subtitled_video.py .
sudo -u shorts cp ../../youtube_downloader.py .

log_success "Python environnement configuré"

###############################################################################
# 8. CRÉER .env
###############################################################################

echo ""
echo "======================================================================"
echo "⚙️  Étape 8/10: Configuration environnement"
echo "======================================================================"

cat > /home/shorts/Test-Omni-Videos/saas/backend/.env << EOF
API_HOST=0.0.0.0
API_PORT=8000
OUTPUT_DIR=/home/shorts/videos_output
DATABASE_URL=postgresql://shorts:ShortsDBPass2024!@localhost/shorts_db
REDIS_URL=redis://localhost:6379/0
EOF

chown shorts:shorts /home/shorts/Test-Omni-Videos/saas/backend/.env

# Créer dossier output
mkdir -p /home/shorts/videos_output
chown -R shorts:shorts /home/shorts/videos_output

log_success "Configuration créée"

###############################################################################
# 9. SETUP SYSTEMD SERVICE
###############################################################################

echo ""
echo "======================================================================"
echo "🔧 Étape 9/10: Configuration service systemd"
echo "======================================================================"

cat > /etc/systemd/system/shorts-api.service << 'EOF'
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
EOF

# Recharger systemd
systemctl daemon-reload

# Activer et démarrer
systemctl enable shorts-api
systemctl start shorts-api

# Attendre que le service démarre
sleep 3

# Vérifier le status
if systemctl is-active --quiet shorts-api; then
    log_success "Service API démarré"
else
    log_error "Service API n'a pas démarré"
    log_info "Vérifiez les logs: sudo journalctl -u shorts-api -n 50"
fi

###############################################################################
# 10. SETUP NGINX
###############################################################################

echo ""
echo "======================================================================"
echo "🌐 Étape 10/10: Configuration Nginx"
echo "======================================================================"

# Demander si l'utilisateur a un domaine
echo ""
read -p "Avez-vous un nom de domaine? (o/N): " -n 1 -r
echo
HAS_DOMAIN=$REPLY

if [[ $HAS_DOMAIN =~ ^[OoYy]$ ]]; then
    read -p "Nom de domaine (ex: shorts.example.com): " DOMAIN
    SERVER_NAME="$DOMAIN"
else
    # Récupérer l'IP publique
    PUBLIC_IP=$(curl -s ifconfig.me)
    SERVER_NAME="$PUBLIC_IP"
    log_info "Utilisation de l'IP: $PUBLIC_IP"
fi

# Créer config Nginx
cat > /etc/nginx/sites-available/shorts << EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    client_max_body_size 500M;

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
    }

    # Docs API
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }

    # Health check
    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    # Frontend
    location /app/ {
        alias /home/shorts/Test-Omni-Videos/saas/frontend/;
        try_files \$uri \$uri/ /app/index.html;
        index index.html;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/shorts /etc/nginx/sites-enabled/

# Supprimer default si existe
rm -f /etc/nginx/sites-enabled/default

# Tester config
nginx -t

# Recharger Nginx
systemctl reload nginx

log_success "Nginx configuré"

# Setup SSL si domaine
if [[ $HAS_DOMAIN =~ ^[OoYy]$ ]]; then
    echo ""
    log_info "Configuration SSL..."
    log_info "Assurez-vous que votre domaine pointe vers cette IP: $PUBLIC_IP"
    echo ""
    read -p "Continuer avec Certbot? (o/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" || log_info "Certbot échoué - configurez manuellement"
    fi
fi

###############################################################################
# 11. FIREWALL
###############################################################################

echo ""
echo "======================================================================"
echo "🔒 Configuration Firewall"
echo "======================================================================"

# Setup UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Enable (sans confirmation interactive)
echo "y" | ufw enable

log_success "Firewall configuré"

###############################################################################
# FINALISATION
###############################################################################

echo ""
echo "======================================================================"
echo "🎉 INSTALLATION TERMINÉE !"
echo "======================================================================"
echo ""

log_success "SaaS YouTube to Shorts installé avec succès !"
echo ""
echo "📊 Informations importantes:"
echo ""
echo "  🌐 URL d'accès:"
if [[ $HAS_DOMAIN =~ ^[OoYy]$ ]]; then
    echo "     https://$DOMAIN"
    echo "     https://$DOMAIN/docs (API Documentation)"
else
    echo "     http://$PUBLIC_IP"
    echo "     http://$PUBLIC_IP/docs (API Documentation)"
fi
echo ""
echo "  🔑 Credentials PostgreSQL:"
echo "     User: shorts"
echo "     Pass: ShortsDBPass2024!"
echo "     DB: shorts_db"
echo ""
echo "  👤 User système:"
echo "     User: shorts"
echo "     Pass: ShortsPass2024!"
echo ""
echo "  📁 Chemins importants:"
echo "     Code: /home/shorts/Test-Omni-Videos"
echo "     Vidéos: /home/shorts/videos_output"
echo "     Logs: /home/shorts/api.log"
echo ""
echo "  🔧 Commandes utiles:"
echo "     • Voir logs API: sudo journalctl -u shorts-api -f"
echo "     • Redémarrer API: sudo systemctl restart shorts-api"
echo "     • Status services: sudo systemctl status shorts-api"
echo ""
echo "⚠️  ACTION REQUISE:"
echo "  1. Changez les mots de passe par défaut !"
echo "  2. Testez l'accès dans votre navigateur"
if [[ ! $HAS_DOMAIN =~ ^[OoYy]$ ]]; then
    echo "  3. Modifiez saas/frontend/index.html ligne 179:"
    echo "     const API_URL = 'http://$PUBLIC_IP';"
fi
echo ""
echo "======================================================================"
echo "✅ Installation complète - Votre SaaS est en ligne !"
echo "======================================================================"
echo ""
