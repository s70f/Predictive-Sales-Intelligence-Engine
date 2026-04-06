# Defining how to find the database
from sqlalchemy import create_engine
import pandas as pd
import subprocess
import os

# Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE
PASS = os.getenv('DB_PASSWORD')
DB_URL = f"postgresql://admin:{PASS}@localhost:5432/dental_clinic"

engine = create_engine(DB_URL)


def ingest_data(file_path, table_name):
    df = pd.read_csv(file_path)
    df.to_sql(table_name, engine, if_exists='replace', index=False)

    print(f"Successfully uploaded {len(df)} rows to {table_name}")


def run_dbt():
    print("Starting dbt transformation")

    result = subprocess.run(
        ["dbt", "run"], cwd="./dental_dbt", capture_output=True, text=True)

    if result.returncode == 0:
        print("dbt transformation complete")
    else:
        print("dbt Error:")
        print(result.stderr)


if __name__ == '__main__':

    ingest_data('./raw_transaction.csv', 'raw_transacations')
    # ingest_data('./inventory.csv', 'raw_inventory')

    run_dbt()
    print("Monthly Update Complete! New Data is now loaded in.")

    # Import -> Connect -> Ingest -> Run dbt
