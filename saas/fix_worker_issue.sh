#!/bin/bash

###############################################################################
# Fix Multi-Worker Job Storage Issue
# Change de 4 workers à 1 worker pour résoudre le problème "Job introuvable"
###############################################################################

set -e

echo "======================================================================"
echo "🔧 Fix Multi-Worker Issue - Passage à 1 Worker"
echo "======================================================================"
echo ""

# Vérifier si on est root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root"
    echo "Utilisez: sudo bash fix_worker_issue.sh"
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/shorts-api.service"

# Vérifier que le fichier existe
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Fichier service introuvable: $SERVICE_FILE"
    exit 1
fi

echo "📋 État actuel du service:"
cat "$SERVICE_FILE"
echo ""
echo "----------------------------------------------------------------------"
echo ""

# Backup
BACKUP_FILE="${SERVICE_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
echo "💾 Backup du fichier service vers: $BACKUP_FILE"
cp "$SERVICE_FILE" "$BACKUP_FILE"
echo ""

# Modifier le fichier pour utiliser 1 worker au lieu de 4
echo "🔄 Modification: -w 4 → -w 1"
sed -i 's/-w 4/-w 1/g' "$SERVICE_FILE"
echo ""

echo "📋 Nouveau contenu du service:"
cat "$SERVICE_FILE"
echo ""
echo "----------------------------------------------------------------------"
echo ""

# Recharger systemd
echo "🔄 Rechargement de systemd..."
systemctl daemon-reload
echo ""

# Redémarrer le service
echo "🔄 Redémarrage du service shorts-api..."
systemctl restart shorts-api
echo ""

# Attendre 2 secondes
sleep 2

# Vérifier le statut
echo "✅ Statut du service:"
systemctl status shorts-api --no-pager -l
echo ""

echo "======================================================================"
echo "✅ Fix appliqué avec succès!"
echo "======================================================================"
echo ""
echo "💡 Explication:"
echo "   - Avant: 4 workers avec mémoire séparée → jobs perdus"
echo "   - Après: 1 worker avec mémoire unique → tous les jobs accessibles"
echo ""
echo "🧪 Prochaine étape: Tester un téléchargement de vidéo depuis le frontend"
echo ""
echo "📝 Note: Pour production à long terme, considérez:"
echo "   - Redis pour partager l'état entre workers"
echo "   - Ou PostgreSQL pour stocker les jobs"
echo ""
echo "🔙 Le backup est disponible ici: $BACKUP_FILE"
echo ""
