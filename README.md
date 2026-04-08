
---

## Pipeline Architecture: The "On-Demand" ETL
This pipeline is designed as a **Local On-Demand Product**. It doesn't require a 24/7 cloud server, making it cost-effective and privacy-compliant for a small dental company.

### 1. The Tool Stack
* **Storage:** **PostgreSQL** running inside a **Docker** container. This ensures the database is portable and doesn't interfere with the user's computer settings.
* **Orchestration & Ingestion:** **Python**. A master script handles waking up the database, reading QuickBooks CSVs via **Pandas**, and pushing them to Postgres using **SQLAlchemy**.
* **Transformation:** **dbt (Data Build Tool)**. dbt acts as the "Washing Machine," using SQL and Jinja macros to turn messy raw strings into clean, typed data.
* **Environment Management:** **python-dotenv**. Keeps sensitive database credentials out of the code and in a protected `.env` file.

---

### 2. The Data Journey (ETL Flow)
The pipeline follows a specific sequence to ensure data integrity:

1.  **Extract:** The user places a QuickBooks export (`raw_transaction.csv`) into the project root.
2.  **Load (Ingestion):** The Python script uses `df.to_sql(if_exists='replace')`. 
    * *Decision:* We chose **"Replace"** to ensure the database is always a perfect mirror of the latest export, preventing accidental duplicates from multiple uploads.
3.  **Transform (Cleaning):** Python triggers `dbt run`.
    * **Macros:** Custom logic (like `clean_money`) strips symbols ($, ,) and casts strings to numeric values.
    * **Staging:** dbt creates `stg_transactions`, a clean table with proper dates, standardized clinic names, and line-item granularity.

---

### 3. Key Configurations & Decision Log
* **Granularity:** We transitioned from "Order-level" to **"Line-item"** granularity. This ensures that an order containing multiple different products (e.g., Matrix Bands and Articulating Paper) is fully preserved.
* **Security:** * **`.gitignore`:** Configured to block all `.csv` files and `postgres_data/` from GitHub, ensuring no patient or sales data is ever leaked.
    * **Environment Variables:** Passwords are never hardcoded; they are pulled from the local `.env` environment.
* **Idempotency:** The "Nuke and Pave" (Replace) approach allows the accountant to run the script 100 times on the same file without ever corrupting the data.

---

### 4. Maintenance & Troubleshooting
* **Database Access:** If the dashboard can't find data, ensure the Docker container is running (`docker compose up -d`).
* **Schema Changes:** If QuickBooks changes their column names (e.g., "Sales Price" becomes "Unit Cost"), you only need to update the mapping in the `stg_transactions.sql` file.
* **History:** To rebuild the entire 3-year history from scratch, run `dbt run --full-refresh`.

---

Here is the complete architectural documentation for the Sintco Dental AI pipeline. 

This document serves as your "System Design Blueprint," capturing both the components we built and the specific engineering decisions that make this a production-grade system rather than just a weekend script.

---

# 🦷 Sintco Dental AI: System Architecture & Documentation

## Executive Summary
The Sintco Dental AI is a decoupled, full-stack machine learning pipeline designed to assist sales representatives by recommending relevant dental products to clinics. It relies on a collaborative filtering algorithm (ALS) trained on historical purchase data. The system is split into three distinct layers: Model Training (Data Science), Model Serving (FastAPI), and the User Interface (Streamlit).

---

## 1. The Machine Learning Pipeline (`train_model.py`)
This layer handles extracting raw data, building the mathematical matrices, and training the "Brain."

* **Data Source:** Pulls "Golden" data from a local PostgreSQL database (`stg_transactions`) via SQLAlchemy.
* **Algorithm:** Uses `implicit.cpu.als.AlternatingLeastSquares` for collaborative filtering.
* **Tracking:** Utilizes MLflow to log parameters (factors, iterations, regularization), metrics (sparsity), and the model artifacts.
* **The "Dictionary" Lock:** Saves both the trained model (`als_model.npz`) **and** the exact Sparse Matrix (`training_matrix.npz`) to disk. This is a critical feature to prevent "ID Drift"—ensuring that Clinic #9 during training is always Clinic #9 during inference.

## 2. The Serving Engine (`main.py`)
A headless, high-performance REST API built with FastAPI that acts as the bridge between the AI model and any internal company software.

### Key Architectural Decisions:
* **Lifespan Pattern:** The model, sparse matrix, and product/clinic lists are loaded into RAM (`app.state`) exactly once when the server boots. This guarantees hyper-fast response times (milliseconds) because the system never hits the hard drive or runs heavy SQL queries during a request.
* **Data Contracts:** Uses Pydantic (`BaseModel`) to guarantee structured JSON responses. Instead of parallel lists, it returns distinct "Objects" for every product containing its SKU, Human Name, and AI Match Score.
* **Hash Lookup:** Generates a lookup dictionary (`app.state.product_lookup`) at startup to instantly translate obscure item codes into human-readable product names.

### API Endpoints:
1. `GET /clinics`: Returns an ordered array of all valid clinic names in Title Case. Used to populate the frontend dropdown.
2. `GET /history/{clinic_id}`: Performs a lightning-fast lookup against the loaded Sparse Matrix to return the top 5 most frequently purchased items for a specific clinic.
3. `GET /recommend/{clinic_id}`: Passes the clinic's index and historical row to the ALS model, applies a filter to exclude previously bought items, and returns the top 5 AI predictions with confidence scores.

## 3. The User Interface (`app.py`)
A Streamlit dashboard designed specifically for non-technical sales representatives.

### Key Features:
* **Decoupled Architecture:** The Streamlit app does not contain any machine learning logic or database credentials. It relies entirely on HTTP `requests` to talk to the FastAPI backend.
* **Contextual Display:** Shows "Top Purchase History" and "AI Recommendations" side-by-side, answering the salesperson's immediate question: *"Why is the AI suggesting this?"*
* **UI/UX Refinements:**
    * **Hidden SKUs:** Product IDs are kept in the API data but stripped from the UI to reduce technical noise.
    * **Static Tables:** Uses `st.table` instead of interactive dataframes to prevent long product names (e.g., "3M RelyX Unicem 2...") from being truncated or cut off.
    * **Readable Metrics:** AI confidence scores are multiplied by 100 and formatted as clean percentages (e.g., `34.9%`).
    * **Caching:** Uses `@st.cache_data` for the clinic list so the dropdown loads instantly without pinging the API on every page refresh.

---

## The Request Flow (How it works in production)
1. **Selection:** A sales rep types "Adrian Martinescu" into the Streamlit dropdown.
2. **Translation:** Streamlit finds the index of that name in the array (e.g., Index `9`) and sets the `clinic_id` to `9`.
3. **The Ping:** Streamlit sends concurrent GET requests to `/history/9` and `/recommend/9`.
4. **The Math:** FastAPI uses `app.state` to pull Adrian's historical row from the matrix, runs the ALS mathematical dot-product, and gets 5 integers back (the recommended product IDs).
5. **The Join:** FastAPI translates those 5 integers into real product names using the dictionary lookup and packages it into JSON.
6. **The Render:** Streamlit receives the JSON, formats the UI, and displays the final dashboard.

---

This setup gives you total control. If the data gets updated in QuickBooks, you simply run `train_model.py` to update the `.npz` files, restart FastAPI, and the dashboard is instantly smarter—without ever touching the UI code.