#!/bin/bash
#
# Setup Cookie Pool - Configuration automatique du pool de cookies YouTube
# Usage: bash setup_cookie_pool.sh
#

set -e  # Exit on error

echo "=========================================="
echo "🔧 SETUP COOKIE POOL MANAGER"
echo "=========================================="
echo ""

# Variables
COOKIE_POOL_DIR="/home/shorts/cookie_pool"
BACKEND_DIR="/home/shorts/Test-Omni-Videos/saas/backend"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction helper
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Étape 1: Créer le répertoire du pool
echo "[1/6] Création du répertoire cookie pool..."
mkdir -p "$COOKIE_POOL_DIR"
chmod 700 "$COOKIE_POOL_DIR"  # Sécurité: seulement propriétaire
print_success "Répertoire créé: $COOKIE_POOL_DIR"
echo ""

# Étape 2: Installer Playwright (pour auto-refresh)
echo "[2/6] Installation de Playwright..."
if python3 -c "import playwright" 2>/dev/null; then
    print_success "Playwright déjà installé"
else
    print_warning "Installation de Playwright..."
    pip3 install playwright
    playwright install chromium
    print_success "Playwright installé"
fi
echo ""

# Étape 3: Créer le fichier de configuration des comptes
echo "[3/6] Création du fichier de configuration..."
CONFIG_FILE="$COOKIE_POOL_DIR/accounts_config.json"

if [ -f "$CONFIG_FILE" ]; then
    print_warning "Fichier de config existe déjà: $CONFIG_FILE"
    echo "   Contenu actuel conservé"
else
    cat > "$CONFIG_FILE" << 'EOF'
[
  {
    "account_id": "cookies_1",
    "email": "your-email-1@gmail.com",
    "password": "your-password-1",
    "notes": "Compte principal - MODIFIEZ CES VALEURS"
  },
  {
    "account_id": "cookies_2",
    "email": "your-email-2@gmail.com",
    "password": "your-password-2",
    "notes": "Compte secondaire - MODIFIEZ CES VALEURS"
  },
  {
    "account_id": "cookies_3",
    "email": "your-email-3@gmail.com",
    "password": "your-password-3",
    "notes": "Compte tertiaire - MODIFIEZ CES VALEURS"
  }
]
EOF
    chmod 600 "$CONFIG_FILE"  # Sécurité: seulement propriétaire peut lire
    print_success "Fichier de config créé: $CONFIG_FILE"
    print_warning "IMPORTANT: Éditez ce fichier avec vos vrais identifiants YouTube!"
    echo "   nano $CONFIG_FILE"
fi
echo ""

# Étape 4: Tester le cookie refresher
echo "[4/6] Test du Cookie Refresher..."
print_warning "ATTENTION: Éditez d'abord $CONFIG_FILE avec vos identifiants!"
echo "   Puis lancez: python3 $BACKEND_DIR/cookie_refresher.py"
echo ""

# Étape 5: Créer le cron job pour auto-refresh
echo "[5/6] Configuration du cron job (auto-refresh toutes les 12h)..."

CRON_CMD="0 */12 * * * cd $BACKEND_DIR && python3 cookie_refresher.py >> /var/log/cookie_refresh.log 2>&1"

# Vérifier si le cron existe déjà
if crontab -l 2>/dev/null | grep -q "cookie_refresher.py"; then
    print_warning "Cron job déjà configuré"
else
    # Ajouter le cron job
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    print_success "Cron job ajouté: Rafraîchissement toutes les 12h"
    echo "   Logs: /var/log/cookie_refresh.log"
fi
echo ""

# Étape 6: Instructions finales
echo "[6/6] Setup terminé !"
echo ""
echo "=========================================="
echo "📋 PROCHAINES ÉTAPES"
echo "=========================================="
echo ""
echo "1. CONFIGURER VOS COMPTES YOUTUBE:"
echo "   nano $CONFIG_FILE"
echo ""
echo "2. RAFRAÎCHIR LES COOKIES MANUELLEMENT (1ère fois):"
echo "   cd $BACKEND_DIR"
echo "   python3 cookie_refresher.py"
echo ""
echo "3. VÉRIFIER LE POOL:"
echo "   python3 cookie_pool_manager.py"
echo ""
echo "4. TESTER AVEC UNE VIDÉO:"
echo "   # Via l'API SaaS, aucun cookie à uploader !"
echo ""
echo "=========================================="
echo "⚙️  CONFIGURATION ACTUELLE"
echo "=========================================="
echo ""
echo "Répertoire pool:    $COOKIE_POOL_DIR"
echo "Config comptes:     $CONFIG_FILE"
echo "Backend dir:        $BACKEND_DIR"
echo "Cron job:           Toutes les 12h"
echo "Rate limiting:      100 requêtes/heure/compte"
echo "Total capacité:     300 requêtes/heure (3 comptes)"
echo ""
echo "=========================================="
echo "✅ SETUP COMPLET"
echo "=========================================="
echo ""

print_warning "N'oubliez pas d'éditer $CONFIG_FILE avec vos vrais identifiants YouTube!"
