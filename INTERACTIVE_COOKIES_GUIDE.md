# 🍪 Guide: Capture Interactive de Cookies YouTube

## 📖 Vue d'ensemble

Ce système permet de capturer automatiquement les cookies YouTube de manière **user-friendly** : un navigateur s'ouvre, vous vous connectez normalement, et les cookies sont capturés automatiquement !

**Fini les exports manuels de cookies !** 🎉

## ✨ Fonctionnalités

- ✅ **100% automatique** : Ouverture du navigateur, capture des cookies, fermeture
- ✅ **User-friendly** : Interface graphique normale de YouTube
- ✅ **Sécurisé** : Les cookies sont stockés localement avec permissions restrictives (600)
- ✅ **Intégré** : Fonctionne automatiquement quand des cookies sont nécessaires
- ✅ **Fallback intelligent** : S'active seulement si le Cookie Pool est vide

## 🔄 Comment ça marche ?

### Scénario 1 : Téléchargement de vidéo

```python
from saas.backend.youtube_downloader import download_video

# Pas besoin de gérer les cookies manuellement !
download_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_path="/path/to/output.mp4"
)
```

**Ce qui se passe** :
1. Le système vérifie le Cookie Pool
2. Si aucun cookie disponible → **Ouverture automatique du navigateur**
3. Vous vous connectez à YouTube normalement
4. Une fois connecté, les cookies sont capturés automatiquement
5. Le navigateur se ferme
6. Le téléchargement continue avec vos cookies

### Scénario 2 : Téléchargement de sous-titres

```python
from saas.backend.youtube_downloader import download_youtube_subtitles

# Pareil, tout est automatique !
subtitles = download_youtube_subtitles(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    language="fr"
)
```

**Ce qui se passe** :
1. Essaie d'abord sans cookies (beaucoup de vidéos publiques)
2. Si échec → Essaie avec Cookie Pool
3. Si échec → **Ouverture automatique du navigateur**
4. Vous vous connectez à YouTube
5. Nouvelle tentative avec vos cookies

## 🧪 Test manuel

Pour tester la capture interactive directement :

```bash
# Test complet avec script dédié
python test_interactive_capture.py

# OU directement via le module
python saas/backend/interactive_cookie_capture.py test_user
```

**Résultat attendu** :
```
🌐 CAPTURE INTERACTIVE DE COOKIES YOUTUBE
======================================================================

📋 Instructions:
  1. Une fenêtre de navigateur va s'ouvrir
  2. Connectez-vous à votre compte YouTube
  3. Une fois connecté, les cookies seront capturés automatiquement
  4. Le navigateur se fermera automatiquement

⏳ Ouverture du navigateur...
📍 Navigation vers YouTube...
✅ Navigateur ouvert!
👤 Veuillez vous connecter à votre compte YouTube...

... [vous vous connectez] ...

✅ Connexion détectée!
📥 Extraction des cookies...
✅ Cookies sauvegardés: /home/shorts/cookie_pool/cookies/test_user_cookies.txt
📊 Nombre de cookies: 24

======================================================================
✨ CAPTURE TERMINÉE AVEC SUCCÈS!
======================================================================
```

## 📁 Fichiers créés

Les cookies sont sauvegardés dans deux formats :

### Format Netscape (utilisé par yt-dlp)
```
/home/shorts/cookie_pool/cookies/user_cookies.txt
```
Compatible avec `yt-dlp`, `curl`, `wget`, etc.

### Format JSON (référence)
```
/home/shorts/cookie_pool/cookies/user_cookies.json
```
Contient les métadonnées (date de capture, etc.)

Les deux fichiers ont des permissions restrictives (`chmod 600`) pour la sécurité.

## 🔧 Architecture

### Fichiers principaux

1. **`saas/backend/interactive_cookie_capture.py`**
   - Module de capture interactive
   - Utilise Playwright pour ouvrir un navigateur
   - Détecte automatiquement la connexion
   - Sauvegarde au format Netscape

2. **`saas/backend/youtube_downloader.py`**
   - Intégration transparente
   - Appelle automatiquement la capture si besoin
   - Fallback intelligent Cookie Pool → Interactive Capture

3. **`test_interactive_capture.py`**
   - Script de test autonome
   - Vérifie que tout fonctionne

### Détection de connexion

Le système attend que ces cookies d'authentification apparaissent :
- `LOGIN_INFO` : Présent quand connecté
- `SAPISID`, `APISID` : Cookies de session API YouTube
- `SSID`, `SID` : Cookies de session Google

**Timeout** : 5 minutes (largement suffisant pour se connecter)

## 🚀 Installation

### Prérequis

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Installer le navigateur Chromium pour Playwright
playwright install chromium

# (Optionnel) Installer les dépendances système pour Playwright
playwright install-deps chromium
```

### Vérification

```bash
# Vérifier que Playwright fonctionne
python -c "from playwright.async_api import async_playwright; print('✅ OK')"

# Tester la capture
python test_interactive_capture.py
```

## 📊 Flux de décision

```
┌─────────────────────────────────────┐
│  Demande de téléchargement vidéo    │
└──────────────┬──────────────────────┘
               │
               ▼
     ┌─────────────────────┐
     │ Cookies fournis ?   │
     └─────┬───────────┬───┘
           │ OUI       │ NON
           ▼           ▼
     ┌─────────┐   ┌──────────────────┐
     │ Utilise │   │ Cookie Pool ?    │
     └─────────┘   └────┬────────┬────┘
                        │ OUI    │ NON
                        ▼        ▼
                  ┌─────────┐  ┌────────────────────┐
                  │ Utilise │  │ Capture Interactive│
                  └─────────┘  │  (navigateur)      │
                               └──────────┬─────────┘
                                          ▼
                                   ┌──────────────┐
                                   │ Télécharge   │
                                   └──────────────┘
```

## 💡 Avantages vs autres méthodes

| Méthode | User-friendly | Automatique | Sécurisé |
|---------|--------------|-------------|----------|
| **Export manuel cookies** | ❌ Non (compliqué) | ❌ Non | ⚠️ Moyen |
| **Cookie Pool automatique** | ✅ Oui | ✅ Oui | ⚠️ Stocke credentials |
| **Capture Interactive** | ✅✅ Très ! | ✅ Oui | ✅✅ Très (pas de credentials stockés) |

## 🔐 Sécurité

- ✅ Pas de stockage de mot de passe
- ✅ Permissions restrictives sur les fichiers cookies (600)
- ✅ Cookies expirés automatiquement selon YouTube
- ✅ Navigateur contrôlé localement (pas de cloud)
- ✅ Headers réalistes pour éviter la détection

## 🆘 Dépannage

### Le navigateur ne s'ouvre pas

```bash
# Réinstaller Chromium
playwright install chromium

# Installer les dépendances système
playwright install-deps chromium
```

### Timeout lors de la connexion

Le timeout est de 5 minutes. Si vous dépassez :
- Vérifiez votre connexion internet
- Essayez de vous connecter plus rapidement
- Vérifiez que vous n'avez pas de 2FA qui bloque

### Les cookies ne sont pas détectés

Le système attend au moins 3 cookies d'authentification parmi :
- LOGIN_INFO, SAPISID, APISID, SSID, SID

Si vous êtes connecté mais les cookies ne sont pas détectés :
- Actualisez la page YouTube dans le navigateur
- Naviguez vers une vidéo
- Attendez quelques secondes

## 📝 Logs de debug

Le système affiche des logs détaillés :

```
[DEBUG] URL: https://www.youtube.com/watch?v=...
[DEBUG] Cookies: /path/to/cookies.txt (exists: True)
[DEBUG] Starting download...
[DEBUG] Video title: Ma Super Vidéo
[DEBUG] Available formats count: 24
```

## 🎯 Cas d'usage

### Utilisation ponctuelle
Parfait pour les utilisateurs qui téléchargent occasionnellement.

### Utilisation fréquente
Le Cookie Pool reste préférable (plus rapide, pas d'interaction).

### Environnement serveur
La capture interactive **nécessite un environnement graphique**.
Sur serveur headless → utiliser le Cookie Pool.

### Environnement local
**Idéal !** Interface graphique disponible, expérience utilisateur optimale.

## 🔄 Workflow recommandé

### Sur votre PC local
→ Utiliser **Capture Interactive** (user-friendly)

### Sur serveur avec interface graphique
→ Utiliser **Cookie Pool** + Capture Interactive en fallback

### Sur serveur headless (VPS, Docker, etc.)
→ Utiliser **Cookie Pool uniquement** (avec refresh automatique)

---

**Questions ?** Consultez les logs détaillés lors de l'exécution ou testez avec `test_interactive_capture.py` ! 🚀
