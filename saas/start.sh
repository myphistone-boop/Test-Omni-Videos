#!/bin/bash

echo "🚀 Démarrage du SaaS YouTube to Shorts"
echo "======================================"
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérifier FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg n'est pas installé"
    echo "   Installer avec: sudo apt install ffmpeg (Linux)"
    echo "   Ou: brew install ffmpeg (Mac)"
    exit 1
fi

echo "✅ Python: $(python3 --version)"
echo "✅ FFmpeg: $(ffmpeg -version | head -n 1)"
echo ""

# Créer dossier output
mkdir -p /tmp/shorts_output
echo "✅ Dossier output créé: /tmp/shorts_output"
echo ""

# Installer dépendances backend si nécessaire
if [ ! -d "backend/venv" ]; then
    echo "📦 Installation des dépendances backend..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✅ Dépendances installées"
    echo ""
fi

# Démarrer backend
echo "🔧 Démarrage du backend API..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Attendre que le backend démarre
sleep 3

# Démarrer frontend
echo "🎨 Démarrage du frontend..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "✅ SaaS démarré avec succès !"
echo "======================================"
echo ""
echo "📡 Backend API: http://localhost:8000"
echo "   Documentation: http://localhost:8000/docs"
echo ""
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "Pour arrêter:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Ou utilisez Ctrl+C puis:"
echo "  pkill -f 'uvicorn|http.server'"
echo ""

# Garder le script actif
wait
