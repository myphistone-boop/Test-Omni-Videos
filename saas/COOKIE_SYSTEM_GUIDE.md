# 🍪 Guide complet du système de gestion des cookies

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Upload initial du cookie](#upload-initial-du-cookie)
3. [Cookie Keeper - Maintien en vie](#cookie-keeper---maintien-en-vie)
4. [Most Replayed Scraper](#most-replayed-scraper)
5. [Logs et monitoring](#logs-et-monitoring)
6. [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

Le système comprend **3 composants** :

### 1. **Cookie Monitor** (`cookie_monitor.py`)
- Vérifie la santé du cookie
- API `/api/cookie-status` pour le frontend
- Stocke l'état dans `cookie_status.json`

### 2. **Cookie Keeper** (`cookie_keeper.py`)
- Maintient le cookie en vie
- Visite YouTube toutes les 2-3h
- Utilise Playwright pour simuler un humain

### 3. **Most Replayed Scraper** (`most_replayed_scraper.py`)
- Extrait les moments les plus visionnés
- Utilise Playwright + cookies
- Retourne les timestamps avec scores

---

## 📤 Upload initial du cookie

### Option 1 : Via le frontend (Recommandé)

1. Ouvre http://184.174.36.43/
2. Tu vois : "🔴 Cookie invalide" ou "⚙️ Aucun cookie"
3. Clique sur "📤 Uploader un cookie YouTube"
4. Sélectionne ton fichier `cookies.txt`
5. ✅ Validé !

### Option 2 : Manuellement via SCP

```bash
# Sur ton PC
scp cookies.txt root@184.174.36.43:/home/shorts/cookies/account_1.txt
```

---

## 🔄 Cookie Keeper - Maintien en vie

### Installation du cron job

```bash
# Sur le serveur
cd /home/shorts/Test-Omni-Videos/saas/backend
chmod +x setup_cookie_keeper_cron.sh
bash setup_cookie_keeper_cron.sh
```

### Ce que ça fait

```
Toutes les 2 heures (avec offset random 0-30 min) :
├─ Lance Playwright
├─ Charge le cookie
├─ Visite YouTube
├─ Scroll 2-4 fois (20-30 secondes)
├─ Récupère le cookie mis à jour
└─ Sauvegarde le cookie
```

### Test manuel

```bash
# Test AVEC interface (debug)
python3 cookie_keeper.py --duration 30

# Test sans interface (production)
python3 cookie_keeper.py --headless --duration 30
```

### Logs

```bash
# Voir les logs du cookie keeper
tail -f /var/log/cookie-keeper.log

# Voir les exécutions récentes
grep "COOKIE KEEPER" /var/log/cookie-keeper.log | tail -10
```

---

## 🎬 Most Replayed Scraper

### Utilisation

```python
from most_replayed_scraper import get_most_replayed_moments

moments = get_most_replayed_moments(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    cookie_file="/home/shorts/cookies/account_1.txt",
    headless=True
)

if moments:
    print(f"✅ {len(moments)} moments trouvés")
    for m in moments:
        print(f"  {m['start']:.1f}s - {m['end']:.1f}s (score: {m['score']:.2f})")
else:
    print("⚠️  Aucun moment trouvé (vidéo pas assez populaire)")
```

### Test en ligne de commande

```bash
# Avec interface (debug)
python3 most_replayed_scraper.py "https://www.youtube.com/watch?v=VIDEO_ID" \
  --cookie-file /home/shorts/cookies/account_1.txt

# Sans interface (production)
python3 most_replayed_scraper.py "https://www.youtube.com/watch?v=VIDEO_ID" \
  --cookie-file /home/shorts/cookies/account_1.txt \
  --headless
```

### Sortie

```json
[
  {
    "start": 45.3,
    "end": 68.7,
    "score": 0.92
  },
  {
    "start": 120.1,
    "end": 145.8,
    "score": 0.85
  }
]
```

---

## 📊 Logs et monitoring

### Logs disponibles

```bash
# Backend principal
tail -f /home/shorts/api-error.log

# Cookie keeper
tail -f /var/log/cookie-keeper.log

# Requêtes HTTP
tail -f /home/shorts/api.log
```

### Ce que tu vois dans les logs

#### **Téléchargement avec cookie** :

```
🎬 Tentative de téléchargement...
🍪 Cookie serveur trouvé et utilisé automatiquement
[DEBUG] URL: https://www.youtube.com/watch?v=...
[DEBUG] Cookies: /home/shorts/cookies/account_1.txt (exists: True)
[DEBUG] Video title: Ma vidéo
✅ Download complete
```

#### **Sous-titres trouvés** :

```
🎬 Récupération DIRECTE des sous-titres YouTube...
   Mode: AVEC cookies
🔍 [STEP 1] Essai langue 'fr' - Type: manual
   [STEP 1.1] URL construite (MANUELS): https://...
   [STEP 2] Requête envoyée - Code HTTP: 200
   [STEP 6.3] ✓ 1234 événements trouvés
✅✅✅ SUCCÈS: 5678 mots extraits (manual)!
```

#### **Sous-titres FR non trouvés** :

```
======================================================================
❌ AUCUN SOUS-TITRE TROUVÉ
======================================================================
📝 Langue demandée: fr
🔍 Variantes testées: fr, fr-CA, fr-FR, en
🎯 Types testés: manuel + auto-généré

💡 Raisons possibles:
   • La vidéo n'a pas de sous-titres dans cette langue
   • Les sous-titres sont désactivés par le créateur

💬 Message utilisateur:
   ⚠️ Aucun sous-titre français trouvé pour cette vidéo.
   Les sous-titres YouTube ne sont pas disponibles en français.
   Vous pouvez réessayer avec une autre vidéo ou utiliser le mode Whisper (payant).
======================================================================
```

#### **Cookie Keeper** :

```
======================================================================
🍪 COOKIE KEEPER - 2026-01-14 15:30:45
======================================================================
📂 Cookie file: /home/shorts/cookies/account_1.txt
🎭 Headless: True
⏱️  Durée visite: 30s

🚀 [STEP 1] Lancement du navigateur...
✅ Navigateur lancé
🌐 [STEP 2] Création du contexte...
🍪 [STEP 3] Chargement des cookies...
✅ 23 cookies injectés
📄 [STEP 4] Ouverture de la page YouTube...
✅ Page YouTube chargée
📜 [STEP 6] Simulation activité humaine (scroll)...
   Scroll 1/3 : 542px
   Scroll 2/3 : 678px
   Scroll 3/3 : 423px
💾 [STEP 7] Récupération des cookies mis à jour...
✅ 25 cookies récupérés
💾 [STEP 8] Sauvegarde des cookies...
✅ 25 cookies sauvegardés
======================================================================
✅ COOKIE KEEPER : SUCCÈS
======================================================================
⏰ Durée totale : 30s
📅 Prochain refresh recommandé : dans 2-3 heures
```

---

## 🔍 Monitoring en temps réel

### Dashboard frontend

Le frontend affiche :

```
╔════════════════════════════════════════╗
║ 🟢 Cookie valide                       ║
║ Cookie rafraîchi par le keeper         ║
║ ████████████████████████ 100/100       ║
║                                        ║
║ 📊 Score: 100/100 | ⏰ Âge: 2.3 h     ║
║ 🔍 Dernière vérif: il y a 15 min      ║
╚════════════════════════════════════════╝
```

### API de statut

```bash
# Vérifier le statut du cookie
curl http://localhost:8000/api/cookie-status | python3 -m json.tool

# Retourne:
{
  "status": "ok",
  "message": "Cookie rafraîchi avec succès par le keeper",
  "last_check": "2026-01-14T15:30:45",
  "last_success": "2026-01-14T15:30:45",
  "created_at": "2026-01-14T10:00:00",
  "age_hours": 5.5,
  "health_score": 100
}
```

---

## 🛠️ Dépannage

### Cookie invalide

**Symptôme** : "🔴 Cookie invalide"

**Solutions** :

1. **Re-upload un nouveau cookie** :
   ```bash
   # Sur ton PC, exporte un nouveau cookie.txt
   # Puis upload via le frontend ou SCP
   ```

2. **Vérifier le fichier** :
   ```bash
   # Sur le serveur
   ls -lh /home/shorts/cookies/account_1.txt
   head -5 /home/shorts/cookies/account_1.txt
   ```

3. **Test manuel** :
   ```bash
   python3 cookie_monitor.py
   ```

### Cookie Keeper ne se lance pas

**Symptôme** : Logs vides dans `/var/log/cookie-keeper.log`

**Solutions** :

1. **Vérifier le cron** :
   ```bash
   crontab -l | grep cookie_keeper
   ```

2. **Tester manuellement** :
   ```bash
   cd /home/shorts/Test-Omni-Videos/saas/backend
   venv/bin/python3 cookie_keeper.py --headless --duration 10
   ```

3. **Vérifier les permissions** :
   ```bash
   chmod +x cookie_keeper.py
   chmod 644 /var/log/cookie-keeper.log
   ```

### Playwright ne fonctionne pas

**Symptôme** : `Error: executable doesn't exist`

**Solution** :

```bash
cd /home/shorts/Test-Omni-Videos/saas/backend
venv/bin/python3 -m playwright install chromium
venv/bin/python3 -m playwright install-deps
```

### Sous-titres FR toujours non trouvés

**Causes possibles** :

1. **La vidéo n'a vraiment pas de sous-titres FR**
   - Teste avec une vidéo FR populaire (ex: France 24)

2. **Cookie expiré/invalide**
   - Re-upload un nouveau cookie

3. **IP bloquée par YouTube**
   - Vérifie avec : `curl -I https://www.youtube.com`

---

## ✅ Checklist de déploiement

- [ ] Cookie uploadé via frontend ou SCP
- [ ] Statut du cookie "🟢 OK" dans le frontend
- [ ] Cookie Keeper installé (cron job)
- [ ] Playwright installé (`python3 -m playwright install chromium`)
- [ ] Test manuel du cookie keeper réussi
- [ ] Logs visibles dans `/var/log/cookie-keeper.log`
- [ ] Test téléchargement vidéo avec cookie réussi
- [ ] Test scraping sous-titres FR réussi
- [ ] Test scraping moments les plus replays (optionnel)

---

## 🎓 Commandes utiles

```bash
# Tester tout le système
cd /home/shorts/Test-Omni-Videos/saas/backend

# 1. Vérifier le cookie
venv/bin/python3 cookie_monitor.py

# 2. Tester le cookie keeper
venv/bin/python3 cookie_keeper.py --headless --duration 10

# 3. Tester le scraping des moments
venv/bin/python3 most_replayed_scraper.py "URL_VIDEO" \
  --cookie-file /home/shorts/cookies/account_1.txt \
  --headless

# 4. Voir tous les logs en temps réel
tail -f /home/shorts/api-error.log /var/log/cookie-keeper.log
```

---

**Le système est maintenant complet !** 🚀

Tout est automatisé :
- ✅ Upload du cookie via le frontend
- ✅ Vérification du statut en temps réel
- ✅ Maintien en vie automatique (cron)
- ✅ Logs verbeux pour debugging
- ✅ Messages clairs si échec

**Prochaine étape** : Déployer sur le serveur et tester ! 🎯
