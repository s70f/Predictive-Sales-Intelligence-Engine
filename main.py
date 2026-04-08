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


class RecResponse(BaseModel):
    clinic_name: str
    recommendations: List[str]
    scores: List[float]


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

    app.state.clinics = list(matrix.index)
    app.state.products = list(matrix.columns)

    # Dictionary translates IDs to Names
    # ml_models["products"] = {}

    yield  # Server ready

    print("Shutting down")
    engine.dispose()

app = FastAPI(lifespan=lifespan)


@app.get("/recommend/{clinic_id}", response_model=RecResponse)
async def recommend(clinic_id: int):
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

    return {
        "clinic_name": app.state.clinics[clinic_id],
        "recommendations": recommended_names,
        "scores": [float(s) for s in scores]  # Pydantic needs standard floats
    }
