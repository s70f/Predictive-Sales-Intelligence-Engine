import subprocess
import time
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)


def ingest_data(file_path, table_name):
    print(f"Loading {file_path} into database")
    df = pd.read_csv(file_path)
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    print(f"Successfully uploaded {len(df)} rows.")


def run_dbt():
    print("🧹leaning data with dbt")
    result = subprocess.run(
        ["dbt", "run"], cwd="./dental_dbt", capture_output=True, text=True)
    if result.returncode != 0:
        print("dbt Error:\n", result.stderr)
        raise Exception("dbt failed")
    print("Data cleaned.")


def train_model():
    print("Training AI Model")
    subprocess.run(["python", "train_model.py"], check=True)
    print("AI Model updated.")


if __name__ == '__main__':
    api_process = None
    try:
        # 1. Pipeline Steps
        # Update table name to match your setup
        ingest_data('./raw_transaction.csv', 'stg_transactions')
        run_dbt()
        train_model()

        print("System Ready! Launching Dashboard")

        # 2. Launch FastAPI in the background
        api_process = subprocess.Popen(
            ["uvicorn", "main:app", "--port", "8000"])

        # Give the API 3 seconds to boot up before opening the frontend
        time.sleep(3)

        # 3. Launch Streamlit
        subprocess.run(["streamlit", "run", "app.py"])

    except Exception as e:
        print(f"System Error: {e}")

    finally:
        # 4. Cleanup: When they close the dashboard, kill the hidden FastAPI server
        print("Shutting down servers")
        if api_process:
            api_process.terminate()
