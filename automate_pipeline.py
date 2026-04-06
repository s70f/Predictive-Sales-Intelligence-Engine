# Defining how to find the database
from sqlalchemy import create_engine
import pandas as pd
import subprocess
import os
from dotenv import load_dotenv

# Load the variables from the .env file
load_dotenv()

# Get the password from the environment
db_pass = os.getenv('DB_PASSWORD')
db_user = os.getenv('DB_USER')
db_name = os.getenv('DB_NAME')

DB_URL = f"postgresql://{db_user}:{db_pass}@localhost:5432/{db_name}"

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
