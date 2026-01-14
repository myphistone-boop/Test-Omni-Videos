#!/bin/bash
#
# Script pour appliquer le fix des sous-titres auto-générés
# À exécuter sur le serveur Contabo
#

set -e

echo "🔧 Application du fix sous-titres auto-générés YouTube"
echo "======================================================"
echo ""

# Sauvegarder l'état actuel
echo "1️⃣  Sauvegarde de l'état actuel..."
CURRENT_BRANCH=$(git branch --show-current)
echo "   Branche actuelle: $CURRENT_BRANCH"

# Fetch les changements
echo ""
echo "2️⃣  Récupération des modifications..."
git fetch origin claude/fix-contabo-repo-issues-lmiGO

# Merger les changements
echo ""
echo "3️⃣  Application du fix..."
git merge origin/claude/fix-contabo-repo-issues-lmiGO

# Vérifier le merge
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Fix appliqué avec succès!"

    # Redémarrer le service
    echo ""
    echo "4️⃣  Redémarrage du service..."
    systemctl restart shorts-api

    echo ""
    echo "✅ Service redémarré!"
    echo ""
    echo "📝 Pour voir les logs:"
    echo "   journalctl -u shorts-api -f"
else
    echo ""
    echo "❌ Erreur lors du merge"
    exit 1
fi
