import subprocess
import time
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()


def manage_docker(action):
    if action == "start":
        print("Booting up the Database Engine")
        subprocess.run(["docker", "compose", "up", "-d"], check=True)
        print("Waiting for database to initialize")
        time.sleep(5)
    elif action == "stop":
        print("Putting database to sleep")
        subprocess.run(["docker", "compose", "stop"], check=True)


def setup():
    try:
        # 0. Requirements
        print("Installing required Python libraries")
        subprocess.run(
            ["pip", "install", "-r", "requirements.txt"], check=True)

        manage_docker("start")

        # 1. Connect to DB
        DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:5432/{os.getenv('DB_NAME')}"
        engine = create_engine(DB_URL)

        # 2. Ingest Data
        print("Ingesting raw QuickBooks CSV into Database")
        df = pd.read_csv('./raw_transaction.csv')
        df.to_sql('stg_transactions', engine, if_exists='replace', index=False)
        print(f"Successfully uploaded {len(df)} rows")

        # 3. Clean Data (dbt)
        print("Cleaning data with dbt")
        subprocess.run(["dbt", "run"], cwd="./dental_dbt", check=True)

        # 4. Train AI Model
        print("Training AI Brain (This may take a minute)")
        subprocess.run(["python", "src/train_model.py"], check=True)

        print("\nSETUP COMPLETE The AI is fully trained and ready for daily use")

    except Exception as e:
        print(f"Setup Failed: {e}")
    finally:
        manage_docker("stop")


if __name__ == '__main__':
    setup()
