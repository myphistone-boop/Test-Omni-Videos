#!/bin/bash
#
# Setup Cookie Keeper Cron Job
# Configure le cron job pour maintenir le cookie en vie toutes les 2-3 heures
#

set -e

echo "========================================"
echo "🍪 SETUP COOKIE KEEPER CRON JOB"
echo "========================================"
echo ""

# Paths
BACKEND_DIR="/home/shorts/Test-Omni-Videos/saas/backend"
PYTHON_BIN="$BACKEND_DIR/venv/bin/python3"
COOKIE_KEEPER_SCRIPT="$BACKEND_DIR/cookie_keeper.py"
LOG_DIR="/var/log"
COOKIE_KEEPER_LOG="$LOG_DIR/cookie-keeper.log"

# Vérifier que les fichiers existent
echo "📂 Vérification des chemins..."
if [ ! -f "$COOKIE_KEEPER_SCRIPT" ]; then
    echo "❌ Script cookie_keeper.py introuvable: $COOKIE_KEEPER_SCRIPT"
    exit 1
fi

if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ Python venv introuvable: $PYTHON_BIN"
    echo "   Veuillez créer le virtualenv d'abord"
    exit 1
fi

echo "✅ Tous les chemins validés"
echo ""

# Créer le fichier log
echo "📝 Création du fichier log..."
touch "$COOKIE_KEEPER_LOG"
chmod 644 "$COOKIE_KEEPER_LOG"
echo "✅ Log file: $COOKIE_KEEPER_LOG"
echo ""

# Préparer le cron job
# Exécute toutes les 2 heures avec un offset aléatoire (via sleep random)
CRON_COMMAND="0 */2 * * * (sleep \$((RANDOM \% 1800)); $PYTHON_BIN $COOKIE_KEEPER_SCRIPT --headless --duration 30) >> $COOKIE_KEEPER_LOG 2>&1"

echo "⏰ Configuration du cron job..."
echo "   Commande: $CRON_COMMAND"
echo ""

# Vérifier si le cron job existe déjà
if crontab -l 2>/dev/null | grep -q "cookie_keeper.py"; then
    echo "⚠️  Un cron job cookie_keeper existe déjà"
    echo "   Voulez-vous le remplacer? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "❌ Installation annulée"
        exit 0
    fi

    # Supprimer l'ancien
    echo "🗑️  Suppression de l'ancien cron job..."
    crontab -l 2>/dev/null | grep -v "cookie_keeper.py" | crontab -
fi

# Ajouter le nouveau cron job
echo "➕ Ajout du nouveau cron job..."
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job installé!"
echo ""

# Afficher le crontab actuel
echo "📋 Crontab actuel:"
echo "========================================"
crontab -l | grep "cookie_keeper" || echo "(aucun cron job cookie_keeper trouvé)"
echo "========================================"
echo ""

# Test manuel
echo "🧪 Test manuel du cookie keeper..."
echo "   Lancement d'un test (sans headless pour debug)..."
echo ""

$PYTHON_BIN $COOKIE_KEEPER_SCRIPT --duration 10 2>&1 | tail -20

echo ""
echo "========================================"
echo "✅ INSTALLATION TERMINÉE"
echo "========================================"
echo ""
echo "📊 Informations:"
echo "   • Script: $COOKIE_KEEPER_SCRIPT"
echo "   • Fréquence: Toutes les 2 heures (avec random offset 0-30 min)"
echo "   • Log file: $COOKIE_KEEPER_LOG"
echo ""
echo "📝 Commandes utiles:"
echo "   • Voir les logs: tail -f $COOKIE_KEEPER_LOG"
echo "   • Lister cron jobs: crontab -l"
echo "   • Éditer cron jobs: crontab -e"
echo "   • Supprimer ce cron: crontab -l | grep -v 'cookie_keeper' | crontab -"
echo ""
echo "🧪 Test manuel:"
echo "   $PYTHON_BIN $COOKIE_KEEPER_SCRIPT --headless --duration 30"
echo ""
