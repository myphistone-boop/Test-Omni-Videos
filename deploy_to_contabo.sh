#!/bin/bash
# Script de déploiement automatique sur Contabo

set -e  # Arrêt en cas d'erreur

echo "🚀 DÉPLOIEMENT DE LA BRANCHE claude/revival-branch-copy-mhTnb"
echo "============================================================"

# Connexion SSH et exécution des commandes
ssh root@184.174.36.43 << 'ENDSSH'

echo "📍 Connexion établie au serveur Contabo"
cd /home/shorts/Test-Omni-Videos

echo ""
echo "📊 État actuel du serveur:"
git branch
git status

echo ""
echo "⏸️  Arrêt des services en cours..."
# Arrêter les services Docker si actifs
if [ -f "saas/docker-compose.yml" ]; then
    cd saas
    docker-compose down 2>/dev/null || true
    cd ..
fi

# Arrêter les processus Python si actifs
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

echo ""
echo "📥 Récupération de la nouvelle branche..."
git fetch origin

echo ""
echo "🔄 Changement vers la branche claude/revival-branch-copy-mhTnb..."
git checkout claude/revival-branch-copy-mhTnb
git pull origin claude/revival-branch-copy-mhTnb

echo ""
echo "📦 Mise à jour des dépendances..."
cd saas/backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt --quiet

echo ""
echo "🚀 Redémarrage des services..."
cd /home/shorts/Test-Omni-Videos/saas

# Option 1: Docker (si configuré)
if [ -f "docker-compose.yml" ]; then
    echo "   → Démarrage via Docker Compose..."
    docker-compose up -d
else
    # Option 2: Systemd service (si configuré)
    if systemctl is-active --quiet shorts-api; then
        echo "   → Redémarrage du service systemd..."
        systemctl restart shorts-api
    else
        # Option 3: Démarrage manuel en background
        echo "   → Démarrage manuel du backend..."
        cd backend
        nohup python3 main.py > /tmp/shorts-api.log 2>&1 &
        echo "   → Backend démarré (logs dans /tmp/shorts-api.log)"
    fi
fi

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ !"
echo "============================================================"
echo "📊 Vérification:"
cd /home/shorts/Test-Omni-Videos
git log --oneline -5
echo ""
echo "🌐 Services actifs:"
netstat -tlnp | grep -E ':(80|443|8000)' || echo "   Aucun service détecté sur les ports 80/443/8000"

ENDSSH

echo ""
echo "🎉 Déploiement terminé avec succès !"
