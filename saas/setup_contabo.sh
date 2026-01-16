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

# Générer mot de passe aléatoire sécurisé
USER_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Vérifier si l'utilisateur existe déjà
if id "shorts" &>/dev/null; then
    log_info "L'utilisateur 'shorts' existe déjà"
else
    # Créer user sans interaction
    useradd -m -s /bin/bash shorts

    # Définir un mot de passe
    echo "shorts:$USER_PASSWORD" | chpasswd

    # Ajouter aux sudoers
    usermod -aG sudo shorts

    log_success "Utilisateur 'shorts' créé"
fi

###############################################################################
# 4. SETUP POSTGRESQL
###############################################################################

echo ""
echo "======================================================================"
echo "🗄️  Étape 4/10: Configuration PostgreSQL"
echo "======================================================================"

# Générer mot de passe database aléatoire
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Démarrer PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Créer database et user
sudo -u postgres psql -c "CREATE USER shorts WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || log_info "User postgres 'shorts' existe déjà"
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

# Demander la clé OpenAI (optionnel, peut être configuré après)
echo ""
log_info "🔑 Clé API OpenAI pour la transcription Whisper"
log_info "Obtenez votre clé sur: https://platform.openai.com/api-keys"
log_info "Coût: ~0.006\$/minute de vidéo"
log_info "Vous pouvez la configurer maintenant OU après avec: bash saas/configure_openai.sh"
echo ""
read -p "Clé OpenAI (sk-...) [appuyez sur Entrée pour configurer après]: " OPENAI_KEY

# Créer le fichier .env avec TOUTES les variables nécessaires
cat > /home/shorts/Test-Omni-Videos/saas/backend/.env << EOF
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
OUTPUT_DIR=/home/shorts/videos_output

# OpenAI Whisper (REQUIS pour fonctionner)
# Configurez avec: bash saas/configure_openai.sh
OPENAI_API_KEY=${OPENAI_KEY:-YOUR_OPENAI_KEY_HERE}

# Database & Cache
DATABASE_URL=postgresql://shorts:$DB_PASSWORD@localhost/shorts_db
REDIS_URL=redis://localhost:6379/0
EOF

chown shorts:shorts /home/shorts/Test-Omni-Videos/saas/backend/.env

# Créer dossier output
mkdir -p /home/shorts/videos_output
chown -R shorts:shorts /home/shorts/videos_output

if [ -z "$OPENAI_KEY" ]; then
    log_success "Configuration créée (configurez OpenAI après avec: bash saas/configure_openai.sh)"
else
    log_success "Configuration créée avec clé OpenAI"
fi

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
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile /home/shorts/api.log \
    --error-logfile /home/shorts/api-error.log

# Note: -w 1 car l'application utilise un stockage en mémoire (jobs_db dict)
# Pour scaler avec plusieurs workers, implémenter PostgreSQL/Redis pour les jobs

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
# CONFIGURER L'URL FRONTEND
###############################################################################

echo ""
echo "======================================================================"
echo "🎨 Configuration URL frontend"
echo "======================================================================"

# Récupérer l'IP publique
PUBLIC_IP=$(curl -s ifconfig.me)

# Déterminer l'URL finale
if [[ $HAS_DOMAIN =~ ^[OoYy]$ ]]; then
    FRONTEND_API_URL="https://$DOMAIN"
else
    FRONTEND_API_URL="http://$PUBLIC_IP"
fi

# Mettre à jour l'URL dans le frontend
FRONTEND_FILE="/home/shorts/Test-Omni-Videos/saas/frontend/index.html"
if [ -f "$FRONTEND_FILE" ]; then
    # Remplacer l'URL hardcodée par l'URL réelle
    sed -i "s|const API_URL = 'http://[0-9.]*';|const API_URL = '$FRONTEND_API_URL';|g" "$FRONTEND_FILE"
    log_success "URL frontend configurée: $FRONTEND_API_URL"
else
    log_error "Fichier frontend introuvable"
fi

###############################################################################
# SAUVEGARDER CREDENTIALS
###############################################################################

echo ""
echo "======================================================================"
echo "💾 Sauvegarde des credentials"
echo "======================================================================"

# Créer fichier de credentials LOCALEMENT sur le serveur
# Ce fichier NE sera JAMAIS committé sur GitHub
cat > /root/.shorts_credentials << EOF
# Credentials YouTube to Shorts SaaS
# Généré le: $(date)
# ⚠️  GARDEZ CE FICHIER SECRET - Ne le partagez JAMAIS

## User système
User: shorts
Password: $USER_PASSWORD

## PostgreSQL
DB User: shorts
DB Password: $DB_PASSWORD
DB Name: shorts_db

## OpenAI API
OpenAI Key: $OPENAI_KEY

## URLs
EOF

if [[ $HAS_DOMAIN =~ ^[OoYy]$ ]]; then
    echo "Public URL: https://$DOMAIN" >> /root/.shorts_credentials
    echo "API Docs: https://$DOMAIN/docs" >> /root/.shorts_credentials
else
    echo "Public URL: http://$PUBLIC_IP" >> /root/.shorts_credentials
    echo "API Docs: http://$PUBLIC_IP/docs" >> /root/.shorts_credentials
fi

# Sécuriser le fichier (lisible que par root)
chmod 600 /root/.shorts_credentials

log_success "Credentials sauvegardés dans /root/.shorts_credentials"

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
echo "  🔑 Credentials:"
echo "     ⚠️  Sauvegardés dans: /root/.shorts_credentials"
echo "     Voir: cat /root/.shorts_credentials"
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
echo "     • Voir credentials: cat /root/.shorts_credentials"
echo ""
echo "⚠️  PROCHAINES ÉTAPES:"
if [ -z "$OPENAI_KEY" ]; then
    echo "  1. 🔑 IMPORTANT: Configurez votre clé OpenAI:"
    echo "     cd /home/shorts/Test-Omni-Videos && bash saas/configure_openai.sh"
    echo "     OU éditez manuellement: /home/shorts/Test-Omni-Videos/saas/backend/.env"
    echo "  2. ✅ Sauvegardez /root/.shorts_credentials dans un lieu sûr"
else
    echo "  1. ✅ Sauvegardez /root/.shorts_credentials dans un lieu sûr"
fi
echo "  2. 🌐 Testez l'API: curl $FRONTEND_API_URL/"
if [[ $HAS_DOMAIN =~ ^[OoYy]$ ]]; then
    echo "  3. 🎨 Accédez au frontend: https://$DOMAIN/app/"
else
    echo "  3. 🎨 Accédez au frontend: http://$PUBLIC_IP/app/"
fi
echo "  4. 🍪 Préparez vos cookies YouTube:"
echo "     - Installez: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
echo "     - Allez sur youtube.com (connecté)"
echo "     - Exportez cookies.txt via l'extension"
echo "  5. 🚀 Testez avec une vidéo courte d'abord (1-2 minutes)"
echo ""
echo "📊 COMMENT VOIR LA PROGRESSION:"
echo "  • Dans le frontend: Barre de progression avec % et étapes"
echo "  • Via logs API: sudo journalctl -u shorts-api -f"
echo "  • Via API direct: curl $FRONTEND_API_URL/api/status/\$JOB_ID"
echo ""
echo "======================================================================"
echo "✅ Installation complète - Votre SaaS YouTube to Shorts est en ligne !"
echo "======================================================================"
echo ""
