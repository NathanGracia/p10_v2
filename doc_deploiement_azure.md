# Déploiement Azure — étapes réalisées

## Vue d'ensemble

On a déployé une **API de recommandation** sur Azure, accessible publiquement via une URL HTTPS. Voici le schéma de ce qu'on a construit :

```
Utilisateur (user_id)
        ↓
Azure Function (HTTP trigger)
  https://p10-recommend-gracia.azurewebsites.net/api/recommend?user_id=12
        ↓
Télécharge le modèle pkl depuis Azure Blob Storage
        ↓
Calcule 5 recommandations
        ↓
Retourne un JSON
```

---

## Étape 1 — Préparer le modèle

**Fichier :** `models/recommendation_artifacts_optimized.pkl` (163 MB)

Ce fichier contient tout ce qu'il faut pour faire des recommandations :
- `user_factors` / `item_factors` : les vecteurs du modèle de Collaborative Filtering (ALS)
- `user2idx` / `idx2article` : les tables de correspondance user_id ↔ index
- `clicks_per_user` : les articles déjà vus par chaque utilisateur (pour les exclure)
- `popular_articles` : liste de 20 articles populaires (fallback cold start)

On avait déjà généré ce fichier via `scripts/optimize_artifacts.py` (conversion float64→float32 pour réduire la taille).

---

## Étape 2 — Se connecter à Azure CLI

```bash
az login --use-device-code --tenant 6be52553-7fe6-4aa6-93b9-8e4f90a92da6
```

**Pourquoi `--use-device-code` ?** Le login standard ouvre un navigateur mais échoue si le compte a le MFA activé. Le mode device code affiche un code à entrer sur `login.microsoft.com/device`, ce qui contourne le problème.

**Pourquoi `--tenant` ?** Sans ça, Azure CLI cherche dans tous les tenants et peut se perdre. On lui indique directement le bon annuaire (celui du compte personnel de Nathan).

---

## Étape 3 — Uploader le modèle sur Azure Blob Storage

**Blob Storage = un stockage de fichiers dans le cloud** (comme un Google Drive mais pour les applis).

Les ressources existaient déjà (créées la session précédente) :
- Groupe de ressources : `p10`
- Storage Account : `p10storagegracia`
- Conteneur : `models`

```bash
az storage blob upload \
  --account-name p10storagegracia \
  --container-name models \
  --name recommendation_artifacts_optimized.pkl \
  --file models/recommendation_artifacts_optimized.pkl \
  --account-key <clé>
```

**Pourquoi `--account-key` et pas `--auth-mode login` ?** Le compte n'a pas les rôles RBAC "Storage Blob Data Contributor" configurés, donc l'authentification par clé est le chemin le plus simple.

---

## Étape 4 — Créer le projet Azure Function en local

```bash
func init --worker-runtime python --python-version 3.11
func new --name recommend --template "HTTP trigger" --authlevel anonymous
```

Ça génère un dossier `azure_function/` avec :
- `function_app.py` : le code de la fonction (modifié ensuite)
- `requirements.txt` : les dépendances Python
- `local.settings.json` : la config locale (variables d'env, ne se déploie pas sur Azure)
- `host.json` : config du runtime Azure Functions

**`--authlevel anonymous`** : l'endpoint est accessible sans clé API. Pratique pour un projet étudiant.

---

## Étape 5 — Coder la fonction

**Fichier :** `azure_function/function_app.py`

Logique :
1. Au premier appel, la fonction télécharge le pkl depuis Blob Storage et le garde en mémoire (`_artifacts` global → cache)
2. Elle lit le `user_id` dans les paramètres de l'URL (ou dans le body JSON)
3. Si le user existe dans le modèle → **Collaborative Filtering** : produit scalaire entre le vecteur user et tous les vecteurs articles, top 5 en excluant les déjà vus
4. Si le user est inconnu → **cold start** : retourne les 5 articles les plus populaires

Réponse JSON :
```json
{
  "user_id": 12,
  "recommendations": [111043, 272218, 234267, 129434, 289003],
  "method": "collaborative_filtering"
}
```

---

## Étape 6 — Tester en local

```bash
func start
curl "http://localhost:7071/api/recommend?user_id=12"
```

Le serveur local simule exactement le comportement Azure. Si ça marche ici, ça marchera dans le cloud.

**Note :** `func start` utilise le Python système (pas le venv), il a fallu installer les dépendances globalement avec `pip install azure-storage-blob numpy`.

---

## Étape 7 — Créer la Function App sur Azure

```bash
az provider register --namespace Microsoft.Web
az functionapp create \
  --resource-group p10 \
  --consumption-plan-location francecentral \
  --runtime python --runtime-version 3.11 \
  --functions-version 4 \
  --name p10-recommend-gracia \
  --storage-account p10storagegracia \
  --os-type linux
```

**`az provider register`** : la première fois qu'on utilise Azure Functions sur un abonnement, il faut "débloquer" le service `Microsoft.Web`. C'est une formalité administrative Azure.

**Plan Consumption** = plan serverless gratuit : la fonction ne tourne que quand elle est appelée, on ne paie que l'exécution (très peu, voire rien sur les quotas gratuits). Pas de serveur allumé en permanence.

---

## Étape 8 — Configurer la variable d'environnement

```bash
az functionapp config appsettings set \
  --name p10-recommend-gracia \
  --resource-group p10 \
  --settings "STORAGE_CONNECTION_STRING=<connection_string>"
```

La fonction a besoin de la connection string pour accéder au Blob Storage. En local, elle est dans `local.settings.json`. Sur Azure, on la passe via les **App Settings** (l'équivalent des variables d'environnement).

---

## Étape 9 — Déployer

```bash
func azure functionapp publish p10-recommend-gracia
```

Ce que fait cette commande :
1. Crée une archive zip du dossier `azure_function/`
2. L'envoie sur Azure
3. Azure fait un **remote build** : installe les dépendances Python sur un container Linux
4. Compresse tout dans un fichier `.squashfs` et l'upload sur Blob Storage
5. Redémarre les workers avec le nouveau code

Durée : ~3 minutes.

---

## Résultat final

**URL publique :**
```
https://p10-recommend-gracia.azurewebsites.net/api/recommend?user_id=<ID>
```

| user_id connu | user_id inconnu |
|---|---|
| Collaborative Filtering | Popularity fallback (cold start) |
| top 5 par score ALS, sans les déjà vus | top 5 articles les plus populaires |

---

## Ressources Azure utilisées (à éteindre après chaque session)

| Ressource | Nom | Coût |
|---|---|---|
| Resource Group | `p10` | gratuit |
| Storage Account | `p10storagegracia` | ~0€/mois (< 1 GB) |
| Function App | `p10-recommend-gracia` | gratuit (plan Consumption) |
| Application Insights | `p10-recommend-gracia` | gratuit (quota) |
