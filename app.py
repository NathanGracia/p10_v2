import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "https://p10-recommend-gracia.azurewebsites.net/api/recommend"

st.set_page_config(page_title="My Content", page_icon="📰", layout="centered")


@st.cache_data
def load_metadata():
    df = pd.read_csv("data/articles_metadata.csv")
    df["date"] = pd.to_datetime(df["created_at_ts"], unit="ms").dt.strftime("%d/%m/%Y")
    return df.set_index("article_id")


metadata = load_metadata()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📰 My Content")
st.caption("Recommandations personnalisées d'articles")
st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    user_id = st.number_input(
        "User ID", min_value=0, step=1, value=12,
        help="Entrez un user_id pour obtenir 5 recommandations"
    )
with col2:
    st.write("")
    st.write("")
    go = st.button("Recommander", type="primary", use_container_width=True)

# ── Appel API ─────────────────────────────────────────────────────────────────
if go:
    with st.spinner("Chargement des recommandations…"):
        try:
            resp = requests.get(API_URL, params={"user_id": int(user_id)}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.Timeout:
            st.error("L'API met trop de temps à répondre (cold start Azure). Réessaie dans 10 secondes.")
            st.stop()
        except Exception as e:
            st.error(f"Erreur API : {e}")
            st.stop()

    method = data["method"]
    reco_ids = data["recommendations"]

    # Badge méthode
    if method == "collaborative_filtering":
        st.success("✅ Recommandations personnalisées — Collaborative Filtering")
    else:
        st.info("🌟 Utilisateur inconnu — Articles populaires (cold start)")

    st.write(f"**5 articles recommandés pour l'utilisateur {user_id} :**")
    st.write("")

    # Cartes articles
    for rank, art_id in enumerate(reco_ids, start=1):
        with st.container(border=True):
            row = metadata.loc[art_id] if art_id in metadata.index else None

            c1, c2 = st.columns([1, 4])
            with c1:
                st.metric("Rang", f"#{rank}")
            with c2:
                st.markdown(f"**Article #{art_id}**")
                if row is not None:
                    cols = st.columns(3)
                    cols[0].caption(f"📂 Catégorie {int(row['category_id'])}")
                    cols[1].caption(f"✍️ {int(row['words_count'])} mots")
                    cols[2].caption(f"📅 {row['date']}")
                else:
                    st.caption("Métadonnées non disponibles")
