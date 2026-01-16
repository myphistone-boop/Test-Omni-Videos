# 🚀 Guide Déploiement Rapide - Serveur Contabo

## 📋 Ce dont vous avez besoin

Avant de commencer, préparez :

1. **Serveur Contabo**
   - VPS avec minimum 4 GB RAM, 2 vCPU
   - Ubuntu 22.04 ou 24.04
   - Accès SSH root

2. **Clé API OpenAI**
   - Obtenez-la sur : https://platform.openai.com/api-keys
   - Format : `sk-proj-...`
   - Coût : ~0.006$/minute de vidéo (~$0.06 pour une vidéo de 10min)

3. **Cookies YouTube** (pour tester après déploiement)
   - Extension Chrome : https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Connectez-vous sur youtube.com
   - Exportez cookies.txt

4. **(Optionnel) Nom de domaine**
   - Si vous voulez HTTPS avec SSL
   - Sinon, utilisez l'IP directement (HTTP)

---

## 🎯 Installation (10 minutes)

### Étape 1 : SSH vers votre serveur

```bash
ssh root@VOTRE_IP_CONTABO
```

### Étape 2 : Cloner le projet

```bash
cd /root
git clone https://github.com/VOTRE_USERNAME/Test-Omni-Videos.git
cd Test-Omni-Videos
```

### Étape 3 : Lancer le script d'installation

```bash
sudo bash saas/setup_contabo.sh
```

Le script va :
- ✅ Installer toutes les dépendances (Python, FFmpeg, PostgreSQL, Redis, Nginx)
- ✅ Créer l'utilisateur `shorts`
- ✅ Configurer la base de données
- ✅ **Vous demander votre clé OpenAI** (préparez-la !)
- ✅ **Vous demander l'URL de votre repo GitHub**
- ✅ **Vous demander si vous avez un domaine** (optionnel)
- ✅ Configurer Nginx + SSL (si domaine)
- ✅ Configurer le firewall
- ✅ Démarrer le service automatiquement

**⏱ Durée : ~10 minutes**

### Étape 4 : Vérifier que tout fonctionne

```bash
# Vérifier le service API
sudo systemctl status shorts-api

# Tester l'API
curl http://localhost:8000/
# Doit retourner: {"status":"online","service":"YouTube to Shorts API"...}
```

### Étape 5 : Récupérer vos credentials

```bash
cat /root/.shorts_credentials
```

**⚠️ SAUVEGARDEZ CE FICHIER dans votre password manager !**

---

## 🎨 Accéder au frontend

### Si vous avez un domaine :
```
https://VOTRE_DOMAINE.com/app/
```

### Si vous utilisez l'IP :
```
http://VOTRE_IP_CONTABO/app/
```

---

## 🧪 Tester avec une vidéo

### 1. Préparer vos cookies YouTube

1. Installez l'extension Chrome : [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Allez sur `youtube.com` et **connectez-vous**
3. Cliquez sur l'extension → **Export** → Sauvegardez `cookies.txt`

### 2. Utiliser le frontend

1. Allez sur `http://VOTRE_IP/app/` (ou votre domaine)
2. Entrez une **URL YouTube courte** (1-2 minutes pour le premier test)
   - Exemple : `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. Sélectionnez la langue : **Français** ou **English**
4. Sélectionnez la plateforme : **TikTok**, **YouTube Shorts** ou **Instagram**
5. **Uploadez votre fichier cookies.txt** (obligatoire)
6. Cliquez sur **🚀 Générer le Short**

### 3. Voir la progression

Le frontend affiche automatiquement :
- ✅ Barre de progression (0-100%)
- ✅ Message de l'étape en cours :
  - "Téléchargement de la vidéo..."
  - "Extraction du segment viral..."
  - "Génération des sous-titres..."
  - "Création du short optimisé..."
  - "Finalisation..."

**⏱ Temps estimé : 2-8 minutes selon la longueur**

### 4. Télécharger le résultat

Quand le statut passe à **✅ Short généré avec succès !** :
- Cliquez sur **📥 Télécharger le Short**
- Le fichier MP4 (format 9:16) se télécharge automatiquement

---

## 📊 Monitoring & Debug

### Voir les logs en temps réel

```bash
# Logs du service API
sudo journalctl -u shorts-api -f

# Logs dans le fichier
tail -f /home/shorts/api.log
tail -f /home/shorts/api-error.log
```

### Redémarrer le service

```bash
sudo systemctl restart shorts-api
```

### Vérifier l'état des services

```bash
# API
sudo systemctl status shorts-api

# PostgreSQL
sudo systemctl status postgresql

# Redis
sudo systemctl status redis-server

# Nginx
sudo systemctl status nginx
```

### Voir tous les jobs en cours

Via l'API :
```bash
curl http://localhost:8000/api/jobs
```

### Voir la progression d'un job spécifique

```bash
curl http://localhost:8000/api/status/JOB_ID
```

---

## 🔧 Commandes utiles

```bash
# Voir les credentials sauvegardés
cat /root/.shorts_credentials

# Voir les vidéos générées
ls -lh /home/shorts/videos_output/

# Espace disque utilisé
df -h

# Mémoire utilisée
free -h

# Processus en cours
htop

# Redémarrer tous les services
sudo systemctl restart shorts-api nginx postgresql redis-server
```

---

## ⚠️ Limitations actuelles

### 🔴 1 seul job à la fois

Le système est configuré avec **1 worker** (pour l'instant) :
- ✅ **1 vidéo traitée à la fois**
- ⏳ Les autres sont mises en queue
- 💡 Pour scaler : implémenter PostgreSQL pour stocker les jobs

### 📦 Stockage local

- Les vidéos sont stockées localement dans `/home/shorts/videos_output/`
- Pensez à nettoyer régulièrement :

```bash
# Supprimer les vidéos de plus de 7 jours
find /home/shorts/videos_output -type f -mtime +7 -delete
```

---

## 💰 Coûts estimés

| Volume | Serveur Contabo | OpenAI Whisper | Total/mois |
|--------|----------------|----------------|------------|
| **5 vidéos/jour** (10min moy.) | 3-4€ | ~$9 | ~13€ |
| **20 vidéos/jour** | 6-8€ | ~$36 | ~44€ |
| **50 vidéos/jour** | 6-8€ | ~$90 | ~98€ |

---

## 🆘 Problèmes fréquents

### ❌ "Job not found"

**Cause** : Le service a redémarré (jobs en mémoire perdus)

**Solution** : Relancez le job

### ❌ "Erreur lors du téléchargement YouTube"

**Cause** : Cookies manquants ou expirés

**Solution** :
1. Régénérez vos cookies sur youtube.com
2. Uploadez le nouveau fichier

### ❌ "OpenAI API error"

**Cause** : Clé API invalide ou quota dépassé

**Solution** :
1. Vérifiez votre clé : https://platform.openai.com/api-keys
2. Vérifiez votre usage : https://platform.openai.com/usage
3. Vérifiez que votre carte bancaire est active

### ❌ Le frontend ne charge pas

**Cause** : Nginx mal configuré ou URL incorrecte

**Solution** :
```bash
# Vérifier Nginx
sudo nginx -t
sudo systemctl restart nginx

# Vérifier l'URL dans le frontend
grep "const API_URL" /home/shorts/Test-Omni-Videos/saas/frontend/index.html
```

### ❌ "Service failed to start"

**Cause** : Erreur dans la configuration

**Solution** :
```bash
# Voir les logs d'erreur
sudo journalctl -u shorts-api -n 50 --no-pager

# Vérifier le .env
cat /home/shorts/Test-Omni-Videos/saas/backend/.env

# Tester manuellement
cd /home/shorts/Test-Omni-Videos/saas/backend
source venv/bin/activate
python main.py
```

---

## 🔐 Sécurité

### ⚠️ À faire avant de mettre en production :

1. **Restreindre CORS**
   - Modifier `saas/backend/main.py` ligne 30
   - Remplacer `allow_origins=["*"]` par votre domaine

2. **Ajouter authentification API**
   - Actuellement : Aucune auth (n'importe qui peut soumettre)
   - Recommandé : Ajouter API keys ou JWT

3. **SSL/HTTPS** (si pas déjà fait)
   - Obligatoire pour un domaine public
   - Utilisez Let's Encrypt (gratuit) via Certbot

4. **Firewall**
   - ✅ Déjà configuré par le script (UFW)
   - Ports ouverts : 22 (SSH), 80 (HTTP), 443 (HTTPS)

---

## 🚀 Pour aller plus loin

### Améliorer les performances

1. **Scaler avec plusieurs workers**
   - Implémenter stockage jobs dans PostgreSQL/Redis
   - Passer à `-w 4` dans le service systemd

2. **Ajouter Celery pour async**
   - Files d'attente distribuées
   - Meilleure gestion de la charge

3. **Monitoring avancé**
   - Sentry pour tracking erreurs
   - Prometheus + Grafana pour métriques

### Ajouter des fonctionnalités

- Upload automatique sur YouTube (déjà codé, pas intégré)
- Upload sur TikTok/Instagram via API
- Batch processing (plusieurs vidéos d'un coup)
- Webhooks de notification
- Interface admin pour gérer les jobs

---

## 📞 Support

- **Documentation complète** : Voir `/DEPLOYMENT.md` et `/CONTABO_DEPLOYMENT.md`
- **API Docs interactives** : `http://VOTRE_IP/docs`
- **Logs** : `sudo journalctl -u shorts-api -f`

---

**✅ C'est tout ! Votre système YouTube to Shorts est maintenant en ligne.**

🎉 **Bon shortage !** 🎬
