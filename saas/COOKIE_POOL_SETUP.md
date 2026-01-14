# Cookie Pool Manager - Documentation Complète

## 🎯 Vue d'ensemble

Le **Cookie Pool Manager** est un système centralisé de gestion des cookies YouTube pour votre SaaS. Il permet de télécharger des vidéos et sous-titres YouTube **sans que l'utilisateur ait à uploader ses cookies**.

### Avantages

✅ **Zéro maintenance manuelle** - Cookies auto-rafraîchis toutes les 12h
✅ **Scalable** - 3-5 comptes = 100-300 requêtes/heure (sûr)
✅ **Fiable** - Rate limiting + health monitoring + quarantaine auto
✅ **Simple** - Utilisateurs n'uploadent plus de cookies
✅ **Sécurisé** - Rotation automatique + détection de ban

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│         COOKIE POOL MANAGER (Singleton)         │
├─────────────────────────────────────────────────┤
│ • Pool de 3-5 comptes YouTube                   │
│ • Rotation round-robin                          │
│ • Rate limiting: 100 req/h par compte           │
│ • Health monitoring + quarantaine auto          │
│ • Auto-refresh via Playwright (cron 12h)        │
└─────────────────────────────────────────────────┘
         ↓                  ↓                  ↓
    Account 1          Account 2          Account 3
  (cookies_1.txt)   (cookies_2.txt)   (cookies_3.txt)
```

---

## 🚀 Installation Rapide

### Sur le serveur Contabo

```bash
# 1. Aller dans le répertoire saas
cd /home/shorts/Test-Omni-Videos/saas

# 2. Lancer le script de setup
bash setup_cookie_pool.sh

# 3. Configurer vos comptes YouTube
nano /home/shorts/cookie_pool/accounts_config.json

# 4. Rafraîchir les cookies (1ère fois)
cd /home/shorts/Test-Omni-Videos/saas/backend
python3 cookie_refresher.py

# 5. Vérifier que ça marche
python3 cookie_pool_manager.py
```

---

## ⚙️ Configuration des Comptes

### Fichier: `/home/shorts/cookie_pool/accounts_config.json`

```json
[
  {
    "account_id": "cookies_1",
    "email": "votre-email-1@gmail.com",
    "password": "votre-mot-de-passe-1",
    "notes": "Compte principal"
  },
  {
    "account_id": "cookies_2",
    "email": "votre-email-2@gmail.com",
    "password": "votre-mot-de-passe-2",
    "notes": "Compte secondaire"
  },
  {
    "account_id": "cookies_3",
    "email": "votre-email-3@gmail.com",
    "password": "votre-mot-de-passe-3",
    "notes": "Compte tertiaire"
  }
]
```

### ⚠️ Recommandations pour les comptes

1. **Utilisez des comptes Google séparés** (pas votre compte principal)
2. **Désactivez 2FA** (ou utilisez codes de sauvegarde)
3. **Vérifiez les comptes** (connexion manuelle 1 fois)
4. **Permissions 600** sur le fichier config (sécurité)

```bash
chmod 600 /home/shorts/cookie_pool/accounts_config.json
```

---

## 🔄 Auto-Refresh des Cookies

### Cron Job (configuré automatiquement)

Le script `setup_cookie_pool.sh` configure un cron job qui rafraîchit les cookies **toutes les 12 heures**.

```bash
# Voir le cron actuel
crontab -l

# Logs du refresh
tail -f /var/log/cookie_refresh.log
```

### Rafraîchir manuellement

```bash
cd /home/shorts/Test-Omni-Videos/saas/backend

# Mode headless (production)
python3 cookie_refresher.py

# Mode visible (debug)
python3 cookie_refresher.py --visible

# Créer config exemple
python3 cookie_refresher.py --create-config
```

---

## 📈 Monitoring du Pool

### Vérifier le status

```bash
cd /home/shorts/Test-Omni-Videos/saas/backend
python3 cookie_pool_manager.py
```

**Output exemple :**

```json
{
  "total_accounts": 3,
  "healthy_accounts": 3,
  "quarantined_accounts": 0,
  "total_requests": 245,
  "total_success": 243,
  "total_failures": 2,
  "success_rate": "99.2%",
  "uptime_hours": 12.5,
  "accounts": [
    {
      "account_id": "cookies_1",
      "is_healthy": true,
      "in_quarantine": false,
      "requests_last_hour": 45,
      "max_requests_per_hour": 100,
      "total_requests": 82,
      "total_errors": 1,
      "error_rate": "1.2%"
    },
    ...
  ]
}
```

### API Endpoint - Statistiques Pool

```bash
# Depuis votre backend FastAPI
curl http://localhost:8000/api/pool/stats
```

---

## 🛡️ Rate Limiting & Sécurité

### Configuration par défaut

- **100 requêtes/heure par compte** (sûr, pas de ban)
- **Rotation round-robin** (équilibre la charge)
- **Quarantaine automatique** après 3 échecs consécutifs (1h)
- **Ban detection** (403/429 → quarantaine 2h)

### Modifier le rate limit

Éditez `cookie_pool_manager.py` :

```python
self.max_requests_per_hour = 100  # Modifier ici
```

### Capacités théoriques

| Comptes | Req/h par compte | Total req/h | Shorts/h | Shorts/jour |
|---------|------------------|-------------|----------|-------------|
| 3       | 100              | 300         | 150      | 3,600       |
| 5       | 100              | 500         | 250      | 6,000       |

**Note :** 1 short = 2 requêtes YouTube (download vidéo + sous-titres)

---

## 🔧 Intégration dans le Code

### Automatique dans `youtube_downloader.py`

Le Cookie Pool est utilisé **automatiquement** si aucun `cookies_path` n'est fourni :

```python
from youtube_downloader import download_video, download_youtube_subtitles

# Utilise automatiquement le pool
download_video("https://youtube.com/watch?v=...", "/tmp/video.mp4")

# Sous-titres avec pool automatique
subs = download_youtube_subtitles("https://youtube.com/watch?v=...", "fr")
```

### API Backend - Aucun changement nécessaire

```bash
# Avant (upload cookies requis)
curl -X POST http://localhost:8000/api/process \
  -F "video_url=https://youtube.com/watch?v=..." \
  -F "cookies_file=@cookies.txt"  # REQUIS avant

# Maintenant (pool automatique, aucun cookie à uploader)
curl -X POST http://localhost:8000/api/process \
  -F "video_url=https://youtube.com/watch?v=..."  # ✅ Ça suffit !
```

---

## 🚨 Dépannage

### Problème : "Cookie Pool vide ou saturé"

**Cause :** Tous les comptes ont atteint leur limite de 100 req/h

**Solutions :**
1. Attendre 1h (le pool se vide automatiquement)
2. Ajouter plus de comptes dans `accounts_config.json`
3. Augmenter `max_requests_per_hour` (risque ban)

### Problème : "Compte en quarantaine"

**Cause :** 3 échecs consécutifs ou détection de ban (403/429)

**Solutions :**
1. Vérifier les logs : `tail -f /var/log/cookie_refresh.log`
2. Rafraîchir les cookies manuellement : `python3 cookie_refresher.py`
3. Vérifier que le compte n'est pas banni sur YouTube

### Problème : "Sign in to confirm you're not a bot"

**Cause :** Cookies expirés ou YouTube détecte un comportement bot

**Solutions :**
1. Rafraîchir les cookies : `python3 cookie_refresher.py`
2. Vérifier que le compte fonctionne manuellement (navigateur)
3. Diminuer le rate limit si trop agressif

### Problème : Playwright ne s'installe pas

```bash
# Installer manuellement
pip3 install playwright
playwright install chromium

# Si erreur de dépendances (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
  libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
  libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

---

## 📊 Logs & Monitoring

### Logs du Cookie Refresher

```bash
# Voir les logs
tail -f /var/log/cookie_refresh.log

# Logs détaillés
cat /var/log/cookie_refresh.log | grep "ERROR\|SUCCÈS"
```

### Logs du Backend SaaS

```bash
# Logs de l'API
journalctl -u shorts-backend -f

# Voir les requêtes du pool
grep "Cookie Pool" /var/log/...
```

---

## 🔐 Sécurité

### Permissions fichiers

```bash
# Config comptes (contient mots de passe)
chmod 600 /home/shorts/cookie_pool/accounts_config.json

# Cookies
chmod 600 /home/shorts/cookie_pool/*.txt

# Répertoire pool
chmod 700 /home/shorts/cookie_pool
```

### Recommandations

1. **NE JAMAIS committer les cookies** (déjà dans `.gitignore`)
2. **Utiliser comptes secondaires** (pas votre compte Google principal)
3. **Chiffrer le disque** si données sensibles
4. **Limiter accès SSH** au serveur

---

## 🎓 Comment ça marche ?

### 1. Initialisation

Au démarrage du backend, le `CookiePoolManager` (singleton) :
- Scanne `/home/shorts/cookie_pool/` pour trouver `cookies_*.txt`
- Crée un objet `CookieAccount` par fichier
- Initialise le rate limiting et health monitoring

### 2. Requête utilisateur

Quand un utilisateur demande un short :
1. `download_video()` est appelé avec `cookies_path=None`
2. Le pool est interrogé : `get_cookie_for_request()`
3. Round-robin : sélectionne le compte suivant
4. Vérifie rate limit + health
5. Retourne le chemin vers `cookies_X.txt`

### 3. Après la requête

Le résultat (succès/échec) est enregistré :
- **Succès** → compteur +1, reset erreurs
- **Échec** → compteur erreurs +1
- **3 échecs** → quarantaine 1h
- **403/429** → quarantaine 2h (ban détecté)

### 4. Auto-refresh (cron)

Toutes les 12h, le cron lance `cookie_refresher.py` :
1. Lit `accounts_config.json`
2. Pour chaque compte :
   - Lance Playwright (navigateur headless)
   - Se connecte à YouTube
   - Extrait les cookies
   - Sauvegarde au format Netscape
3. Le pool recharge automatiquement les nouveaux cookies

---

## 📝 Fichiers du Système

```
saas/backend/
├── cookie_pool_manager.py      # Gestionnaire central du pool
├── cookie_refresher.py          # Auto-refresh via Playwright
├── youtube_downloader.py        # Intégration pool (modifié)
└── main.py                      # API sans upload cookies (modifié)

saas/
├── setup_cookie_pool.sh         # Script d'installation
└── COOKIE_POOL_SETUP.md         # Cette documentation

/home/shorts/cookie_pool/
├── accounts_config.json         # Config comptes (SENSIBLE)
├── cookies_1.txt                # Cookies compte 1
├── cookies_2.txt                # Cookies compte 2
└── cookies_3.txt                # Cookies compte 3
```

---

## 🆘 Support

### Questions fréquentes

**Q: Combien de comptes recommandés ?**
R: 3-5 comptes suffisent pour 100-300 req/h (safe)

**Q: Peut-on utiliser des comptes avec 2FA ?**
R: Non, désactivez 2FA ou utilisez codes de sauvegarde

**Q: Les cookies expirent après combien de temps ?**
R: ~2-4 semaines, mais auto-refresh toutes les 12h

**Q: Que faire si YouTube ban un compte ?**
R: Le pool le met en quarantaine auto. Changez de compte ou attendez.

**Q: Peut-on augmenter à 1000 req/h ?**
R: Risqué. Préférez ajouter plus de comptes (10-15) à 100 req/h chacun.

---

## ✅ Checklist de Mise en Production

- [ ] `setup_cookie_pool.sh` exécuté
- [ ] 3+ comptes configurés dans `accounts_config.json`
- [ ] Cookies rafraîchis manuellement (1ère fois)
- [ ] Cron job actif (`crontab -l`)
- [ ] Pool testé (`python3 cookie_pool_manager.py`)
- [ ] Permissions 600 sur fichiers sensibles
- [ ] Logs accessibles (`/var/log/cookie_refresh.log`)
- [ ] Backend redémarré avec nouveau code
- [ ] Test end-to-end (créer un short sans upload cookies)

---

**🎉 Votre Cookie Pool est maintenant opérationnel !**

Plus besoin de demander aux utilisateurs d'uploader des cookies. Le système gère tout automatiquement avec rate limiting, health monitoring, et auto-refresh. 🚀
