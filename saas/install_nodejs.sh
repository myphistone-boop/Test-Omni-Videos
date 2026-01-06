#!/bin/bash

###############################################################################
# Script d'installation Node.js pour yt-dlp
# Nécessaire pour résoudre le n-challenge YouTube avec le client web + cookies
###############################################################################

set -e

echo "======================================================================"
echo "🟢 Installation Node.js pour yt-dlp"
echo "======================================================================"
echo ""

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    echo "Utilisez: sudo bash install_nodejs.sh"
    exit 1
fi

# Vérifier si Node.js est déjà installé
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "ℹ️  Node.js est déjà installé: $NODE_VERSION"
    read -p "Voulez-vous réinstaller? (o/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
        echo "✅ Installation annulée - Node.js déjà présent"
        exit 0
    fi
fi

echo "📦 Installation Node.js LTS..."
echo ""

# Installer Node.js via NodeSource
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt-get install -y nodejs

echo ""
echo "======================================================================"
echo "✅ Node.js installé avec succès!"
echo "======================================================================"
echo ""

# Vérifier l'installation
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)

echo "📊 Versions installées:"
echo "  • Node.js: $NODE_VERSION"
echo "  • npm: $NPM_VERSION"
echo ""

echo "🔧 Prochaines étapes:"
echo "  1. Redémarrez le service API:"
echo "     sudo systemctl restart shorts-api"
echo ""
echo "  2. Testez un téléchargement YouTube avec cookies"
echo ""
echo "======================================================================"
echo "✅ Installation terminée!"
echo "======================================================================"
echo ""
