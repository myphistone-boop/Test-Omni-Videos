#!/bin/bash

###############################################################################
# Script simple pour configurer la clé OpenAI après installation
###############################################################################

set -e

echo "======================================================================"
echo "🔑 Configuration clé OpenAI Whisper"
echo "======================================================================"
echo ""

# Vérifier qu'on est root ou shorts
if [ "$EUID" -eq 0 ]; then
    ENV_FILE="/home/shorts/Test-Omni-Videos/saas/backend/.env"
else
    ENV_FILE="$HOME/Test-Omni-Videos/saas/backend/.env"
fi

# Vérifier que le fichier .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Fichier .env introuvable: $ENV_FILE"
    echo "Lancez d'abord le script d'installation setup_contabo.sh"
    exit 1
fi

# Demander la clé
echo "Obtenez votre clé sur: https://platform.openai.com/api-keys"
echo "Format: sk-proj-..."
echo ""
read -p "Clé OpenAI: " OPENAI_KEY

if [ -z "$OPENAI_KEY" ]; then
    echo "❌ Clé OpenAI requise"
    exit 1
fi

# Ajouter ou mettre à jour dans le .env
if grep -q "OPENAI_API_KEY=" "$ENV_FILE"; then
    # Remplacer la ligne existante
    sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_KEY|g" "$ENV_FILE"
    echo "✅ Clé OpenAI mise à jour dans $ENV_FILE"
else
    # Ajouter la ligne
    echo "OPENAI_API_KEY=$OPENAI_KEY" >> "$ENV_FILE"
    echo "✅ Clé OpenAI ajoutée dans $ENV_FILE"
fi

# Redémarrer le service si systemd est utilisé
if systemctl is-active --quiet shorts-api; then
    echo ""
    echo "Redémarrage du service API..."
    sudo systemctl restart shorts-api
    echo "✅ Service redémarré"
fi

echo ""
echo "======================================================================"
echo "✅ Configuration terminée !"
echo "======================================================================"
echo ""
echo "Testez avec: curl http://localhost:8000/"
echo ""
