from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from implicit.cpu.als import AlternatingLeastSquares
import pandas as pd
import scipy.sparse as sparse
from pydantic import BaseModel
from typing import List

from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

load_dotenv()

ml_models = {}


class RecommendationItem(BaseModel):
    code: str
    name: str
    score: float


class RecResponse(BaseModel):
    clinic_name: str
    recommendations: List[RecommendationItem]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server Starting")

    # Loading model
    app.state.model = AlternatingLeastSquares.load(
        "als_model.npz")
    app.state.sparse_data = sparse.load_npz("training_matrix.npz")

    # Loading product and clinic lists
    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
    engine = create_engine(DB_URL)

    df = pd.read_sql("SELECT * FROM stg_transactions", engine)

    # Pruning logic (same as training script)
    clinic_counts = df['clinic_name'].value_counts()
    active_clinics = clinic_counts[clinic_counts > 1].index
    df_filtered = df[df['clinic_name'].isin(active_clinics)].copy()

    matrix = df_filtered.groupby(
        ['clinic_name', 'item_code']).size().unstack(fill_value=0)

    app.state.clinics = [name.title() for name in list(matrix.index)]
    app.state.products = list(matrix.columns)

    # Dictionary translates IDs to Names
    product_meta_df = pd.read_sql(
        "SELECT DISTINCT item_code, item_name FROM stg_transactions", engine)

    # Create a fast lookup dictionary: { "item_code": "Human Friendly Name" }
    app.state.product_lookup = pd.Series(
        product_meta_df.item_name.values,
        index=product_meta_df.item_code
    ).to_dict()

    yield  # Server ready

    print("Shutting down")
    engine.dispose()

app = FastAPI(lifespan=lifespan)


@app.get("/recommend/{clinic_id}", response_model=RecResponse)
async def recommend(clinic_id: int, request: Request):
    # Check if the ID exists in matrix
    if clinic_id < 0 or clinic_id >= len(app.state.clinics):
        raise HTTPException(
            status_code=404, detail="Clinic ID not found in the model")

    # Model Logic
    ids, scores = app.state.model.recommend(
        userid=clinic_id,
        user_items=app.state.sparse_data[clinic_id],
        N=5,
        filter_already_liked_items=True
    )

    # Map the numeric IDs back to Product Names
    recommended_names = [app.state.products[i] for i in ids]
    # Map the numeric IDs back to Product Names

    recommended_items = []
    for i, score in zip(ids, scores):
        code = request.app.state.products[i]
        # Look up the human name using the code. Default to the code if name is missing.
        name = request.app.state.product_lookup.get(code, "Unknown Product")

        recommended_items.append({
            "code": code,
            "name": name,
            "score": float(score)
        })

    return {
        "clinic_name": request.app.state.clinics[clinic_id],
        "recommendations": recommended_items
    }


@app.get("/clinics", response_model=List[str])
async def get_clinics():
    """Returns full list of clinics sorted by index"""
    return app.state.clinics


@app.get("/history/{clinic_id}")
async def get_purchase_history(clinic_id: int):
    if clinic_id < 0 or clinic_id >= len(app.state.clinics):
        raise HTTPException(status_code=404, detail="Clinic ID not found")

    user_row = app.state.sparse_data[clinic_id]

    purchases = list(zip(user_row.indices, user_row.data))
    purchases.sort(key=lambda x: x[1], reverse=True)

    top_5_history = purchases[:5]

    history_list = []
    for product_id, count in top_5_history:
        code = app.state.products[product_id]
        # Look up the real name
        name = app.state.product_lookup.get(code, "Unknown Product")

        history_list.append({
            "Code": code,
            "Product Name": name,
            "Times Purchased": int(count)
        })

    return {
        "clinic_name": app.state.clinics[clinic_id],
        "history": history_list
    }
