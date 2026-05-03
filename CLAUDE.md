# P10 — Application de recommandation de contenu (OpenClassrooms)

## Contexte projet

Projet de fin de parcours IA chez OpenClassrooms. On joue le rôle de CTO de la start-up fictive **My Content**, qui recommande des articles à ses utilisateurs.

**Objectif MVP** : pour un `user_id` donné, retourner les **5 articles recommandés**.

Estimation : 70 heures de travail.

## Données (`/data`)

| Fichier | Description | Taille |
|---------|-------------|--------|
| `articles_metadata.csv` | 364 047 articles (article_id, category_id, created_at_ts, publisher_id, words_count) | - |
| `articles_embeddings.pickle` | Embeddings vectoriels des articles | **347 MB** (→ ACP nécessaire pour Azure) |
| `clicks_sample.csv` | Échantillon : 1 883 interactions, 707 users, 323 articles | - |
| `clicks.zip` | Dataset complet des interactions | 36 MB |

### Colonnes clicks
- `user_id`, `session_id`, `session_start`, `session_size`
- `click_article_id`, `click_timestamp`
- `click_environment`, `click_deviceGroup`, `click_os`, `click_country`, `click_region`, `click_referrer_type`

## Architecture cible

Deux options proposées par Julien (dev freelance) — toutes deux en **serverless Azure** :

- **Option A** : API (expose le modèle) + Azure Function (pont entre app et API)
- **Option B** : Azure Function + Azure Blob Storage input binding (sans API séparée) ← plus simple

## Stack technique

- **Python** (pandas, scikit-learn, numpy)
- **Modélisation** : Content-Based Filtering + Collaborative Filtering (Surprise ou Implicit)
- **Cloud** : Azure Functions + Azure Blob Storage (plan Consumption = gratuit)
- **Frontend** : Streamlit ou Flask
- **Versioning** : Git + GitHub

## Livrables

1. Application (Streamlit/Flask + Azure Function déployée)
2. Scripts versionnés sur GitHub
3. Présentation PDF (15-25 slides)

## Roadmap

1. Setup (GitHub, venv)
2. EDA sur les données
3. Modélisation (Content-Based + Collaborative Filtering, comparer, gérer cold start)
4. Déploiement Azure (Blob Storage + Azure Function)
5. Frontend (Streamlit)
6. Présentation
7. Prep soutenance

## Points d'attention

- `articles_embeddings.pickle` est trop lourd pour Azure gratuit → faire une **ACP** avant upload
- Gérer le **cold start** (nouveaux users / nouveaux articles) dans l'architecture cible
- Couper les services Azure après chaque session pour éviter la facturation
