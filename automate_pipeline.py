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

# def manage_docker(action):
#     """Starts or stops the database container."""
#     if action == "start":
#         print("Waking up the database...")
#         # '-d' runs it in the background
#         subprocess.run(["docker", "compose", "up", "-d"], check=True)
#         # Give Postgres a few seconds to 'boot up' before we talk to it
#         time.sleep(5)
#     else:
#         print("Putting the database to sleep")
#         # 'stop' keeps the data safe. 'down' is also fine.
#         # NEVER use 'down -v' or you'll delete the data history!
#         subprocess.run(["docker", "compose", "stop"], check=True)


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

# def run_transformations():
#     """Triggers dbt to clean the data."""
#     print("Running dbt cleaning...")
#     # 'cwd' stands for Current Working Directory - tells Python where the dbt folder is
#     subprocess.run(["dbt", "run"], cwd="./dental_dbt", check=True)


if __name__ == '__main__':

    try:
        # manage_docker("start")
        ingest_data('./raw_transaction.csv', 'raw_transacations')
        # ingest_data('./inventory.csv', 'raw_inventory')

        # run_transformations()
        run_dbt()

        print("Your data is now clean and ready for analysis.")

        # Here is where to launch the Sales Dashboard
        # subprocess.run(["streamlit", "run", "dashboard.py"])

    except Exception as e:
        print(f"Something went wrong: {e}")

    finally:
        # manage_docker("stop")
        pass
