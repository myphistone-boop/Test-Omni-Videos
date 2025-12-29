# ⚡ Quick Start - 5 Minutes

Lancez le SaaS YouTube to Shorts en 5 minutes !

---

## 🚀 Option 1: Script Automatique (Recommandé)

```bash
cd saas
chmod +x start.sh
./start.sh
```

**Ensuite:**
1. Ouvrez http://localhost:3000
2. Collez une URL YouTube
3. Cliquez "Générer le Short"
4. Téléchargez le résultat !

---

## 🛠️ Option 2: Manuel

### Terminal 1: Backend

```bash
cd saas/backend
pip install -r requirements.txt
python main.py
```

### Terminal 2: Frontend

```bash
cd saas/frontend
python -m http.server 3000
```

### Browser

Ouvrez http://localhost:3000

---

## 🐳 Option 3: Docker

```bash
cd saas
docker-compose up
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

---

## 🧪 Tester l'API

```bash
# Health check
curl http://localhost:8000/

# Lancer processing
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "en",
    "target_platform": "tiktok"
  }'

# Ou utiliser le script de test
python test_api.py
```

---

## 📚 Documentation Complète

- **README.md** - Vue d'ensemble et utilisation
- **DEPLOYMENT.md** - Guide de déploiement production
- **API Docs** - http://localhost:8000/docs (auto-générée)

---

## ❓ Problèmes Communs

### Backend ne démarre pas

```bash
# Vérifier Python
python3 --version  # Doit être 3.9+

# Réinstaller
pip install -r backend/requirements.txt --force-reinstall
```

### FFmpeg manquant

```bash
# Linux/WSL
sudo apt install ffmpeg

# Mac
brew install ffmpeg

# Windows
# Télécharger depuis: https://ffmpeg.org/download.html
```

### Port déjà utilisé

```bash
# Changer le port dans main.py:
uvicorn.run(app, host="0.0.0.0", port=8001)  # 8001 au lieu de 8000

# Ou tuer le processus:
lsof -ti:8000 | xargs kill -9
```

---

## ✅ Vérifier que tout fonctionne

1. ✅ Backend accessible: http://localhost:8000
2. ✅ Frontend accessible: http://localhost:3000
3. ✅ Docs API: http://localhost:8000/docs
4. ✅ Health check retourne `{"status": "online"}`

---

## 🎯 Prochaines Étapes

1. **Tester** avec une vraie vidéo YouTube
2. **Customiser** le frontend (couleurs, logo)
3. **Ajouter** auth + paiements (voir DEPLOYMENT.md)
4. **Déployer** sur Railway/Render (voir DEPLOYMENT.md)

---

**C'est tout ! Votre SaaS est prêt. 🎉**

Pour aller plus loin, consultez README.md et DEPLOYMENT.md.
