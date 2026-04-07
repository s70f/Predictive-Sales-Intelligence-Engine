import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

import implicit
from scipy.sparse import csr_matrix
import mlflow

# Load db credentials
load_dotenv()
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)


def calculate_sparsity(df) -> float:
    """Calculates the sparsity of the data"""
    n_clinics = df['clinic_name'].nunique()
    n_transactions = len(df)
    n_products = df['item_code'].nunique()

    total_possible_interactions = n_clinics * n_products

    # Calculating Sparsity
    sparsity = (1 - (n_transactions / total_possible_interactions)) * 100

    return sparsity


def filter_dataframe():
    """Pulls data from postgres and cleans it"""
    # Pull clean dbt table
    df = pd.read_sql("SELECT * FROM stg_transactions", engine)

    # Preprocess
    # Pruning one time clinics identified in EDA
    clinic_counts = df['clinic_name'].value_counts()
    active_clinics = clinic_counts[clinic_counts > 1].index
    df_filtered = df[df['clinic_name'].isin(active_clinics)].copy()

    return df_filtered


def create_user_item_matrix(df_filtered):
    """Create's the user-item matrix needed for ALS algorithm"""

    # Create matrix
    user_item_matrix = df_filtered.groupby(
        ['clinic_name', 'item_code']).size().unstack(fill_value=0)

    return user_item_matrix


def train_recommender(user_item_matrix, df) -> None:

    # Convert user-item matrix to sparse matrix
    sparse_user_item = csr_matrix(user_item_matrix.values)

    # Tracking
    mlflow.set_experiment("Dental_Recommender_Model_A")

    with mlflow.start_run():
        print("Training Model A (ALS Collaborative Filtering)")

        # Initialize model
        model = implicit.als.AlternatingLeastSquares(
            factors=50,
            iterations=20,
            regularization=0.1
        )

        # Fit the model (Transposed because implicit expects item-user matrix)
        model.fit(sparse_user_item.T)

        # Saving parameters and model artifact
        mlflow.log_param("factors", 50)
        mlflow.log_param("iterations", 20)
        mlflow.log_param("regularization", 0.1)
        mlflow.log_param("sparsity", round(calculate_sparsity(df), 2))

        # Save model locally then tell MLflow to track file
        model.save("als_model.npz")
        mlflow.log_artifact("als_model.npz", artifact_path="model")

        print("Trained and logged version to MLflow")


if __name__ == "__main__":

    df_filtered = filter_dataframe()
    user_item_matrix = create_user_item_matrix(df_filtered)
    train_recommender(user_item_matrix, df_filtered)
