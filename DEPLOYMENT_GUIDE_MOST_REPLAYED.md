# 🎬 Guide de déploiement - Most Replayed Scraper

## 📋 Vue d'ensemble

Ce guide vous permet de déployer et tester le nouveau système d'extraction des moments les plus visionnés (most replayed moments) sur le serveur de production.

## 🚀 Étape 1 : Déploiement sur le serveur

### Sur le serveur (184.174.36.43)

```bash
# Se connecter au serveur
ssh root@184.174.36.43

# Aller dans le répertoire du projet
cd /home/shorts/Test-Omni-Videos

# Pull les derniers changements
git fetch origin claude/setup-server-branch-H8EBU
git checkout claude/setup-server-branch-H8EBU
git pull origin claude/setup-server-branch-H8EBU

# Aller dans le backend
cd saas/backend
```

## 🔧 Étape 2 : Installation des dépendances

### Vérifier que le virtualenv existe

```bash
ls -la venv/
```

### Si le venv n'existe pas, le créer :

```bash
python3 -m venv venv
```

### Installer Playwright dans le venv

```bash
venv/bin/pip install playwright
```

### Installer le navigateur Chromium

```bash
venv/bin/python3 -m playwright install chromium
venv/bin/python3 -m playwright install-deps
```

**Note** : La commande `install-deps` peut nécessiter les droits sudo et installer des dépendances système.

## 🧪 Étape 3 : Test du scraper

### Test avec une vidéo populaire (avec interface visible)

Pour débugger, utilisez le mode **non-headless** pour voir le navigateur :

```bash
cd /home/shorts/Test-Omni-Videos/saas/backend

venv/bin/python3 most_replayed_scraper.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --cookie-file /home/shorts/cookies/account_1.txt
```

### Test en mode production (headless)

```bash
venv/bin/python3 most_replayed_scraper.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --cookie-file /home/shorts/cookies/account_1.txt \
  --headless
```

### Test avec une vidéo française populaire

```bash
venv/bin/python3 most_replayed_scraper.py \
  "https://www.youtube.com/watch?v=VIDEO_ID_FR_POPULAIRE" \
  --cookie-file /home/shorts/cookies/account_1.txt \
  --headless
```

## 📊 Résultats attendus

### ✅ Succès

Si le scraper fonctionne, vous verrez :

```
======================================================================
🎬 MOST REPLAYED SCRAPER - 2026-01-15 12:00:00
======================================================================
🔗 URL: https://www.youtube.com/watch?v=...
🍪 Cookie: /home/shorts/cookies/account_1.txt
🎭 Headless: True

🚀 [STEP 1] Lancement du navigateur...
✅ Navigateur lancé
🌐 [STEP 2] Création du contexte...
🍪 [STEP 3] Chargement des cookies...
✅ 23 cookies injectés
📄 [STEP 4] Ouverture de la page YouTube...
✅ Page chargée
⏳ [STEP 5] Attente du chargement du player...
📊 [STEP 6] Extraction des infos vidéo...
   📹 Titre: Nom de la vidéo
   ⏱️  Durée: 213s
🔍 [STEP 7] Recherche du SVG heatmap...
   → Hover sur la barre de progression pour déclencher le SVG...
   ✅ Progress bar trouvée
   ✅ Hover effectué
📊 [STEP 8] Extraction du SVG path...
   ✅ SVG path trouvé (1234 caractères)
   📐 Début du path: M5.0,95.2 C5.5,94.8 6.0,94.3...
🔢 [STEP 9] Parsing des coordonnées...
   ✅ 500 coordonnées extraites
📊 [STEP 10] Conversion en moments...
   🔍  45 pics détectés (seuil: y < 80)
   ✅ 3 moments extraits
      • 45.3s - 68.7s (score: 0.92)
      • 120.1s - 145.8s (score: 0.85)
      • 178.2s - 195.4s (score: 0.78)
🔒 [STEP 11] Fermeture du navigateur...

======================================================================
✅ SUCCÈS : 3 moments trouvés
🏆 Meilleur moment : 45.3s - 68.7s (score: 0.92)
======================================================================

📊 Résultats JSON :
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
  },
  {
    "start": 178.2,
    "end": 195.4,
    "score": 0.78
  }
]
```

### ⚠️ Aucun moment trouvé

Si la vidéo n'a pas assez de vues ou est trop récente :

```
======================================================================
⚠️  AUCUN moment trouvé
======================================================================
💡 Raisons possibles :
   - La vidéo n'a pas assez de vues (< 90k)
   - La vidéo est trop récente (< 5-7 jours)
   - YouTube n'a pas généré de heatmap pour cette vidéo
======================================================================
```

## 🔍 Vidéos de test recommandées

Pour tester, utilisez des vidéos **très populaires** (> 1M de vues, > 1 mois) :

### Vidéos françaises populaires :

1. **France 24** (actualités, beaucoup de vues)
2. **Norman/Cyprien** (YouTubeurs français populaires)
3. **Clips musicaux français** (Jul, Nekfeu, etc.)

### Vidéos internationales :

1. **Rick Astley - Never Gonna Give You Up** : `dQw4w9WgXcQ`
2. **Clips musicaux populaires** (> 100M vues)

### Vidéo de test utilisateur :

1. **https://www.youtube.com/watch?v=5Oo0u5RZ7HA** - Confirmé avoir "Most Replayed" à 1:34

**Note** : Les vidéos doivent avoir suffisamment de données de "replay" pour que YouTube génère le heatmap.

## 🐛 Script de debug (IMPORTANT si le scraper ne trouve rien)

Si le scraper retourne "AUCUN moment trouvé" mais que vous voyez le heatmap dans le navigateur, utilisez le script de debug :

### Mode avec navigateur visible (recommandé pour debug)

```bash
cd /home/shorts/Test-Omni-Videos/saas/backend

venv/bin/python3 debug_heatmap_location.py \
  "https://www.youtube.com/watch?v=5Oo0u5RZ7HA" \
  --cookie-file /home/shorts/cookies/account_1.txt
```

**Sans --headless**, vous verrez le navigateur s'ouvrir et pourrez observer les interactions.

### Ce que le script de debug fait :

1. **Analyse tous les SVG** sur la page principale
2. **Cherche dans les iframes** (le player YouTube est parfois dans un iframe)
3. **Teste différentes interactions** (hover, clic, etc.)
4. **Essaie 7 stratégies différentes** pour localiser le heatmap
5. **Prend un screenshot** dans `/tmp/youtube_heatmap_debug.png`
6. **Affiche des infos détaillées** sur tous les éléments trouvés

### Résultat attendu du debug :

```
======================================================================
🔍 DEBUG HEATMAP LOCATION
======================================================================
URL: https://www.youtube.com/watch?v=5Oo0u5RZ7HA

✅ 23 cookies chargés

⏳ Attente du chargement complet...

======================================================================
📊 STRATÉGIE 1: Tous les SVG sur la page principale
======================================================================
Trouvé 15 SVG sur la page principale:
  #0: classes='...' id='...' parent=DIV paths=5
  ...

======================================================================
📺 STRATÉGIE 2: Chercher dans l'iframe du player YouTube
======================================================================
Trouvé 1 iframe(s) sur la page
  iframe #0: https://www.youtube.com/...
    → 3 SVG dans cette iframe
       #0: classes='ytp-heat-map-svg' ...

======================================================================
🖱️  STRATÉGIE 3: Hover sur la progress bar et attendre
======================================================================
  Essai du sélecteur: .ytp-progress-bar-container
    ✅ Trouvé! Hover...
    ✅ Hover effectué, attente 3s...

======================================================================
🔥 STRATÉGIE 4: Chercher le heatmap après hover
======================================================================
  Essai du sélecteur: svg.ytp-heat-map-svg
    ✅ TROUVÉ!
       Classes: ytp-heat-map-svg
       Has path: True
       Path (début): M5.0,95.2 C5.5,94.8 6.0,94.3...
```

### Si le debug trouve le SVG mais pas le scraper principal :

Cela signifie qu'il faut ajuster les sélecteurs ou les temps d'attente dans `most_replayed_scraper.py`.

### Si le debug ne trouve rien non plus :

1. Vérifier que la vidéo a bien le heatmap dans un navigateur normal
2. Vérifier que le cookie est valide
3. La vidéo n'a peut-être pas assez de vues pour générer le heatmap

## ❌ Problèmes courants

### Problème 1 : Playwright not installed

**Erreur** :
```
ModuleNotFoundError: No module named 'playwright'
```

**Solution** :
```bash
cd /home/shorts/Test-Omni-Videos/saas/backend
venv/bin/pip install playwright
```

### Problème 2 : Chromium not found

**Erreur** :
```
Error: Executable doesn't exist at /home/...
```

**Solution** :
```bash
venv/bin/python3 -m playwright install chromium
venv/bin/python3 -m playwright install-deps
```

### Problème 3 : Cookies invalides

**Erreur** :
```
❌ Fichier cookie introuvable : /home/shorts/cookies/account_1.txt
```

**Solution** :
- Vérifier que le cookie existe : `ls -la /home/shorts/cookies/account_1.txt`
- Re-upload le cookie via le frontend
- Ou copier manuellement : `scp cookies.txt root@184.174.36.43:/home/shorts/cookies/account_1.txt`

### Problème 4 : Aucun SVG trouvé

**Erreur** :
```
❌ Aucun SVG heatmap trouvé dans la page
```

**Raisons possibles** :
1. **Vidéo pas assez populaire** : YouTube génère le heatmap seulement pour les vidéos avec > 90k vues
2. **Vidéo trop récente** : Il faut attendre ~5-7 jours après publication
3. **Mode headless** : Essayer sans `--headless` pour voir ce qui se passe

**Solutions** :
- Tester avec une vidéo **très populaire** (> 1M vues)
- Tester sans `--headless` pour débugger visuellement
- Vérifier que le cookie est valide

## 🎯 Prochaines étapes

### 1. Intégration dans le pipeline principal

Une fois le scraper testé et fonctionnel, l'intégrer dans `video_processor_fast.py` comme fallback :

```python
# Si pas de sous-titres français trouvés
if not subtitles_found:
    print("⚠️ Aucun sous-titre FR trouvé")
    print("🔍 Recherche des moments les plus visionnés...")

    from most_replayed_scraper import get_most_replayed_moments

    moments = get_most_replayed_moments(
        video_url=video_url,
        cookie_file="/home/shorts/cookies/account_1.txt",
        headless=True
    )

    if moments:
        print(f"✅ {len(moments)} moments trouvés!")
        # Utiliser le meilleur moment pour créer le short
        best_moment = moments[0]
        start_time = best_moment['start']
        end_time = best_moment['end']
        # ... découper la vidéo
    else:
        print("❌ Impossible de trouver des moments populaires")
        # Fallback : prendre les 60 premières secondes
```

### 2. Tests automatisés

Créer un script de test qui vérifie régulièrement le fonctionnement :

```bash
#!/bin/bash
# test_most_replayed.sh

cd /home/shorts/Test-Omni-Videos/saas/backend

echo "🧪 Test du Most Replayed Scraper"

venv/bin/python3 most_replayed_scraper.py \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --cookie-file /home/shorts/cookies/account_1.txt \
  --headless

if [ $? -eq 0 ]; then
    echo "✅ Test réussi"
else
    echo "❌ Test échoué"
    exit 1
fi
```

## 📝 Résumé

1. ✅ Pull les changements : `git pull origin claude/setup-server-branch-H8EBU`
2. ✅ Installer Playwright : `venv/bin/pip install playwright`
3. ✅ Installer Chromium : `venv/bin/python3 -m playwright install chromium`
4. ✅ Tester avec vidéo populaire : `venv/bin/python3 most_replayed_scraper.py "URL" --headless`
5. ✅ Vérifier les résultats JSON
6. ✅ Intégrer dans le pipeline principal si succès

## 🆘 Support

Si des problèmes persistent :
- Vérifier les logs : `/home/shorts/shorts-backend-full.log`
- Tester en mode non-headless pour voir le navigateur
- Vérifier que le cookie est valide : `venv/bin/python3 cookie_monitor.py`
- Contacter le support avec les logs complets

---

**Bon déploiement ! 🚀**
