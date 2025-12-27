# 📺 Module d'Upload YouTube Automatique

Module scalable pour uploader automatiquement des vidéos sur YouTube (1 à 10 comptes).

## 🎯 Fonctionnalités

- ✅ Authentification OAuth 2.0 sécurisée
- ✅ Upload automatique de vidéos
- ✅ Génération automatique de métadonnées uniques (titres, descriptions, tags)
- ✅ Support multi-comptes (scalable jusqu'à 10 comptes)
- ✅ Gestion des quotas API
- ✅ Architecture modulaire et maintenable

---

## 📋 Prérequis

### 1. Créer un projet Google Cloud

1. Allez sur https://console.cloud.google.com/
2. Créez un nouveau projet (ex: "YouTube Automation")
3. Activez **YouTube Data API v3** :
   - APIs & Services → Library
   - Recherchez "YouTube Data API v3"
   - Cliquez "Enable"

### 2. Créer les credentials OAuth 2.0

1. APIs & Services → Credentials
2. Create Credentials → OAuth 2.0 Client ID
3. Configure OAuth consent screen si demandé :
   - User Type: External
   - App name: "YouTube Automation"
   - Scopes: Laissez vide pour l'instant
4. Application type: **Desktop app**
5. Name: "YouTube Upload Client"
6. Télécharger le JSON
7. Renommer en `client_secrets.json`
8. Placer dans le dossier racine du projet

---

## 🚀 Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
```

---

## 📝 Configuration

### Étape 1 : Ajouter votre compte dans `accounts_config.py`

Le fichier contient déjà un compte de test. Pour ajouter d'autres comptes :

```python
YOUTUBE_ACCOUNTS = {
    'compte_test_1': {
        'name': 'Mon Compte YouTube',
        'language': 'fr',  # 'fr' ou 'en'
        'credentials_file': 'credentials/compte_test_1.json',
        'upload_time_range': (18, 20),  # Heure optimale
        'enabled': True,
    },
    # Ajouter d'autres comptes ici quand vous scalerez
}
```

### Étape 2 : Authentifier votre compte (1 fois par compte)

```bash
cd youtube_upload
python youtube_auth.py --account compte_test_1
```

**Ce qui se passe** :
1. Une fenêtre de navigateur s'ouvre
2. Connectez-vous avec votre compte YouTube
3. Autorisez l'application
4. Les credentials sont sauvegardés automatiquement

**Vérifier les comptes authentifiés** :
```bash
python youtube_auth.py --list
```

---

## 💻 Utilisation

### Test Léger (RECOMMANDÉ - Avant Upload)

**Avant de faire votre premier upload, testez l'accès au compte avec des actions légères:**

```bash
python test_account_access.py --account compte_test_1
```

**Ce script va:**
- ✅ Vérifier que l'authentification fonctionne
- 📺 Afficher les informations de votre canal (nom, abonnés, statistiques)
- 📋 Lister vos playlists existantes
- 📝 Optionnellement créer/supprimer une playlist de test (pour vérifier le contrôle du compte)
- 📊 Afficher les informations sur les quotas API

**Avantages:**
- 🚀 **Ultra rapide** - Pas besoin de créer une vidéo de test
- 🔒 **Non destructif** - Aucune vidéo uploadée, aucune trace publique
- ✅ **Validation complète** - Vérifie que vous avez bien le contrôle du compte
- 💡 **Infos utiles** - Affiche vos quotas et limites

**Exemple de sortie:**
```
======================================================================
📺 INFORMATIONS DU CANAL
======================================================================

✅ Compte authentifié avec succès !

  📌 Nom du canal: Mon Super Canal
  🆔 Channel ID: UCxxxxxxxxxxxxxxxxx
  📝 Description: Ma chaîne YouTube...

  📊 Statistiques:
     • Abonnés: 1234
     • Vidéos: 10
     • Vues totales: 50000

  🎬 Fonctionnalités:
     • Uploads longs: ✅
     • Shorts: ✅ (disponible pour tous)
     • Posts communautaires: ✅ (>1234 abonnés)
```

---

### Upload d'une vidéo

```bash
python youtube_uploader.py \
  --video /path/to/video.mp4 \
  --title "Titre original de la vidéo YouTube" \
  --account compte_test_1
```

### Exemple complet

```bash
python youtube_uploader.py \
  --video ../output_shorts/video1.mp4 \
  --title "10 Life Hacks Everyone Should Know" \
  --account compte_test_1
```

**Le système va** :
1. Se connecter au compte YouTube
2. Générer automatiquement :
   - Un titre unique et accrocheur
   - Une description optimisée
   - Des tags pertinents
3. Uploader la vidéo
4. Afficher l'URL du Short

---

## 🔧 Utilisation programmatique

### Dans votre code Python

```python
from youtube_upload import YouTubeUploader

# Initialiser
uploader = YouTubeUploader()

# Upload une vidéo
result = uploader.upload_video(
    video_path='output_shorts/video1.mp4',
    original_title='Amazing Life Hack',
    account_id='compte_test_1'
)

if result:
    print(f"✅ Vidéo uploadée: {result['url']}")
```

### Upload en batch

```python
# Liste de vidéos à uploader
videos_data = [
    {
        'video_path': 'output_shorts/video1.mp4',
        'original_title': 'Life Hack 1',
        'account_id': 'compte_test_1',
    },
    {
        'video_path': 'output_shorts/video2.mp4',
        'original_title': 'Life Hack 2',
        'account_id': 'compte_test_1',
    },
]

# Upload avec délai de 60s entre chaque
results = uploader.upload_multiple_videos(
    videos_data,
    delay_between_uploads=60
)
```

---

## 📊 Quotas API YouTube

### Limites

- **10,000 unités/jour** par projet Google Cloud
- 1 upload = **~1,600 unités**
- **Maximum : 6 uploads/jour** par projet

### Solution pour 10 vidéos/jour

Créez **2 projets Google Cloud** :
- Projet 1 : 5 comptes → 5 uploads/jour
- Projet 2 : 5 comptes → 5 uploads/jour

Dans `accounts_config.py`, utilisez différents `client_secrets.json` :

```python
'compte_fr_1': {
    'client_secrets': 'client_secrets_projet1.json',
    ...
},
'compte_fr_6': {
    'client_secrets': 'client_secrets_projet2.json',
    ...
},
```

---

## 🎨 Métadonnées automatiques

Le `MetadataGenerator` crée automatiquement :

### Titres FR
- "{keywords} - Incroyable !"
- "Cette {keywords} va vous choquer"
- "Le secret de {keywords} dévoilé"
- ...

### Titres EN
- "{keywords} - Unbelievable!"
- "This {keywords} will shock you"
- "The secret of {keywords} exposed"
- ...

### Descriptions
- Adaptées à la langue
- Appels à l'action variés
- Hashtags populaires

### Tags
- Extraits du titre original
- Hashtags viraux (#shorts, #viral, #fyp)
- Limité à 15 tags (limite YouTube)

---

## 🔐 Sécurité

- ✅ Credentials OAuth sauvegardés localement (jamais commités)
- ✅ Authentification sécurisée via Google OAuth
- ✅ Tokens rafraîchis automatiquement
- ✅ Fichier `.gitignore` protège les credentials

**Fichiers à NE JAMAIS commiter** :
- `client_secrets.json`
- `credentials/*.json`

---

## 📈 Scaler à 10 comptes

### Étape 1 : Ajouter les comptes dans `accounts_config.py`

```python
YOUTUBE_ACCOUNTS = {
    'compte_fr_1': {...},
    'compte_fr_2': {...},
    'compte_fr_3': {...},
    'compte_fr_4': {...},
    'compte_fr_5': {...},
    'compte_en_1': {...},
    'compte_en_2': {...},
    'compte_en_3': {...},
    'compte_en_4': {...},
    'compte_en_5': {...},
}
```

### Étape 2 : Authentifier tous les comptes

```bash
for account in compte_fr_{1..5} compte_en_{1..5}; do
    python youtube_auth.py --account $account
done
```

### Étape 3 : Utiliser dans votre code

```python
from youtube_upload import get_active_accounts

# Récupérer tous les comptes actifs
accounts = get_active_accounts()

# Ou par langue
accounts_fr = get_accounts_by_language('fr')
accounts_en = get_accounts_by_language('en')
```

---

## ⚠️ Troubleshooting

### Erreur: "client_secrets.json not found"
→ Téléchargez le fichier OAuth depuis Google Cloud Console

### Erreur: "Quota exceeded"
→ Vous avez dépassé les 10,000 unités/jour
→ Attendez demain ou utilisez un 2ème projet Google Cloud

### Erreur: "The user has not granted the app..."
→ Relancez l'authentification avec `--account`

### Erreur de permissions
→ Vérifiez que le compte YouTube a bien autorisé l'application

---

## 📚 Structure du module

```
youtube_upload/
├── __init__.py                    # Exports du module
├── accounts_config.py             # Configuration des comptes (ÉDITER ICI)
├── youtube_auth.py                # Authentification OAuth 2.0
├── youtube_uploader.py            # Upload de vidéos
├── metadata_generator.py          # Génération métadonnées
├── credentials/                   # Credentials OAuth (auto-généré)
│   ├── compte_test_1.json
│   └── ...
└── README.md                      # Cette documentation
```

---

## 🎯 Prochaines étapes

1. ✅ Tester avec 1 compte
2. Valider le concept pendant 1 semaine
3. Scaler à 5 comptes
4. Scaler à 10 comptes
5. Automatiser avec scheduler

---

## 📞 Support

Pour toute question sur le module, consultez :
- Cette documentation
- Le code source (bien commenté)
- La documentation officielle YouTube API
