import azure.functions as func
import json
import logging
import os
import pickle
import io
import numpy as np
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

_artifacts = None


def load_artifacts():
    global _artifacts
    if _artifacts is not None:
        return _artifacts

    conn_str = os.environ["STORAGE_CONNECTION_STRING"]
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_blob_client(
        container="models", blob="recommendation_artifacts_optimized.pkl"
    )

    stream = io.BytesIO()
    blob_client.download_blob().readinto(stream)
    stream.seek(0)
    _artifacts = pickle.load(stream)
    logging.info("Artifacts loaded from Blob Storage")
    return _artifacts


@app.route(route="recommend", auth_level=func.AuthLevel.ANONYMOUS)
def recommend(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Recommendation function triggered.")

    user_id = req.params.get("user_id")
    if not user_id:
        try:
            user_id = req.get_json().get("user_id")
        except ValueError:
            pass

    if not user_id:
        return func.HttpResponse(
            json.dumps({"error": "user_id required"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return func.HttpResponse(
            json.dumps({"error": "user_id must be an integer"}),
            status_code=400,
            mimetype="application/json",
        )

    artifacts = load_artifacts()

    if user_id in artifacts["user2idx"]:
        idx = artifacts["user2idx"][user_id]
        user_vec = artifacts["user_factors"][idx]
        scores = artifacts["item_factors"].dot(user_vec)

        already_clicked = set(artifacts["clicks_per_user"].get(user_id, []))
        ranked_indices = np.argsort(scores)[::-1]

        recommendations = []
        for i in ranked_indices:
            art_id = artifacts["idx2article"][i]
            if art_id not in already_clicked:
                recommendations.append(int(art_id))
                if len(recommendations) == 5:
                    break

        method = "collaborative_filtering"
    else:
        recommendations = [int(a) for a in artifacts["popular_articles"][:5]]
        method = "popularity_fallback"

    return func.HttpResponse(
        json.dumps({
            "user_id": user_id,
            "recommendations": recommendations,
            "method": method,
        }),
        status_code=200,
        mimetype="application/json",
    )
