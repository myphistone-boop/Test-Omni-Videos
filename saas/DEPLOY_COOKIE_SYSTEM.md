# 🍪 Déploiement du système de gestion des cookies

## ✅ Résumé des changements

Le système de gestion des cookies est maintenant **entièrement intégré** :

### Backend
- ✅ **cookie_monitor.py** : Surveillance de la santé des cookies
- ✅ **GET /api/cookie-status** : Vérifie le statut en temps réel
- ✅ **POST /api/upload-cookie** : Upload de cookies via interface web

### Frontend
- ✅ **Statut en temps réel** : Affichage du statut du cookie (🟢 OK / 🔴 Invalide)
- ✅ **Health score** : Barre de progression 0-100
- ✅ **Upload direct** : Bouton pour uploader cookies.txt
- ✅ **Auto-refresh** : Mise à jour automatique toutes les 30 secondes

---

## 📦 Déploiement sur le serveur Contabo

### Étape 1 : Déployer le backend

```bash
# Sur le serveur Contabo
cd /home/shorts/Test-Omni-Videos
git pull origin claude/setup-server-branch-H8EBU

# Redémarrer le backend
bash saas/restart_backend_with_venv.sh
```

### Étape 2 : Déployer le frontend

```bash
# Sur le serveur Contabo
cd /home/shorts/Test-Omni-Videos
bash saas/deploy_frontend.sh
```

### Étape 3 : Tester

```bash
# Test 1: Vérifier que l'API backend fonctionne
curl http://localhost:8000/api/cookie-status

# Devrait retourner:
# {"status":"missing","message":"Aucun cookie configuré",...}

# Test 2: Ouvrir le frontend dans le navigateur
# http://184.174.36.43/

# Vous devriez voir :
# ⚙️ Aucun cookie
# + Bouton "📤 Uploader un cookie YouTube"
```

---

## 🎯 Utilisation du système

### Pour l'administrateur (TOI)

#### 1. **Créer le cookie sur ton PC**

```bash
# Sur ton PC local (avec GUI)
# Option A : Utiliser une extension Chrome/Firefox

1. Installer l'extension "Get cookies.txt LOCALLY"
   - Chrome: https://chrome.google.com/webstore
   - Firefox: https://addons.mozilla.org

2. Aller sur youtube.com
3. Se connecter avec le compte DÉDIÉ au service
4. Cliquer sur l'extension
5. Exporter → Télécharger cookies.txt
```

#### 2. **Uploader le cookie via le frontend**

```
1. Ouvrir http://184.174.36.43/
2. La page affiche : "🔴 Cookie invalide" ou "⚙️ Aucun cookie"
3. Cliquer sur "📤 Uploader un cookie YouTube"
4. Sélectionner le fichier cookies.txt
5. Le système valide et sauvegarde
6. Le statut passe à "🟢 Cookie valide"
```

#### 3. **Vérifier le statut**

Le frontend affiche automatiquement :
- 🟢 **Cookie OK** : Tout fonctionne
- 🔴 **Cookie invalide** : Action requise
- 🟡 **Cookie warning** : À surveiller
- ⚙️ **Aucun cookie** : Upload nécessaire

---

## 🔄 Monitoring automatique

### Cookie keeper (à configurer)

Le système inclut un moniteur de cookies à exécuter régulièrement :

```bash
# Test manuel du monitoring
cd /home/shorts/Test-Omni-Videos/saas/backend
python3 cookie_monitor.py

# Devrait afficher:
# 🔍 Vérification du cookie à 2026-01-14...
# ✅ Cookie valide (ou ❌ Cookie invalide)
# 📊 Health Score: 100/100
```

### Ajouter au cron (plus tard)

```bash
# Éditer crontab
crontab -e

# Ajouter cette ligne pour vérifier toutes les 2 heures
0 */2 * * * cd /home/shorts/Test-Omni-Videos/saas/backend && /home/shorts/Test-Omni-Videos/saas/backend/venv/bin/python3 cookie_monitor.py
```

---

## 🧪 Tests complets

### Test 1 : Statut sans cookie

```bash
# Vérifier que le statut est "missing"
curl http://localhost:8000/api/cookie-status

# Résultat attendu:
{
  "status": "missing",
  "message": "Aucun cookie configuré",
  "health_score": 0
}
```

### Test 2 : Upload d'un cookie

```bash
# Préparer un fichier de test (remplacer par un vrai cookie)
echo "# Netscape HTTP Cookie File
youtube.com	TRUE	/	FALSE	0	test_cookie	test_value" > /tmp/test_cookies.txt

# Upload via API
curl -X POST http://localhost:8000/api/upload-cookie \
  -F "cookie_file=@/tmp/test_cookies.txt"

# Résultat attendu:
{
  "success": true,
  "message": "Cookie uploadé avec succès et marqué comme actif"
}
```

### Test 3 : Vérifier le nouveau statut

```bash
curl http://localhost:8000/api/cookie-status

# Devrait maintenant afficher:
{
  "status": "ok",
  "message": "Cookie uploadé avec succès",
  "health_score": 100,
  "age_hours": 0.0
}
```

### Test 4 : Frontend

1. Ouvrir http://184.174.36.43/
2. Observer le statut du cookie affiché en haut
3. Si "🔴 Invalide" → Bouton upload visible
4. Si "🟢 OK" → Bouton upload caché
5. La health bar doit afficher 0-100%

---

## 📊 Interface utilisateur finale

Voici ce que l'utilisateur (toi) verra :

```
╔═══════════════════════════════════════════╗
║ 🎬 YouTube to Shorts                      ║
╠═══════════════════════════════════════════╣
║                                           ║
║ ┌─────────────────────────────────────┐  ║
║ │ 🟢 Cookie valide                    │  ║
║ │ Cookie uploadé avec succès          │  ║
║ │ ████████████████████░░░░░░ 80/100   │  ║
║ │ 📊 Score: 80/100 | ⏰ Âge: 2.3 h    │  ║
║ └─────────────────────────────────────┘  ║
║                                           ║
║ URL YouTube:                              ║
║ [_________________________________]       ║
║                                           ║
║ [🚀 Générer le Short]                     ║
╚═══════════════════════════════════════════╝
```

**OU** si cookie manquant :

```
╔═══════════════════════════════════════════╗
║ 🎬 YouTube to Shorts                      ║
╠═══════════════════════════════════════════╣
║                                           ║
║ ┌─────────────────────────────────────┐  ║
║ │ 🔴 Cookie invalide !                │  ║
║ │ Action requise immédiatement        │  ║
║ │ ░░░░░░░░░░░░░░░░░░░░░░░ 0/100       │  ║
║ │                                     │  ║
║ │ [📤 Uploader nouveau cookie]       │  ║
║ │ 💡 Tutoriel : Comment obtenir ?     │  ║
║ └─────────────────────────────────────┘  ║
╚═══════════════════════════════════════════╝
```

---

## ✅ Checklist de déploiement

- [ ] Pull les changements sur le serveur
- [ ] Redémarrer le backend
- [ ] Déployer le nouveau frontend
- [ ] Tester l'endpoint /api/cookie-status
- [ ] Ouvrir le frontend dans le navigateur
- [ ] Vérifier l'affichage du statut
- [ ] Tester l'upload d'un cookie
- [ ] Vérifier que le statut passe à "OK"
- [ ] Confirmer le polling automatique (30s)

---

## 🎓 Prochaines étapes

Une fois le système déployé :

1. **Créer ton premier cookie** sur ton PC
2. **L'uploader** via le frontend
3. **Tester un téléchargement** de vidéo YouTube
4. **Configurer le cookie keeper** (cron job 2h)
5. **Ajouter des comptes backup** (optionnel)

---

**Le système est maintenant prêt !** 🚀

Tu peux uploader tes cookies directement depuis le frontend, et le statut sera visible en temps réel.
