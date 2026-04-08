*Note: Permission was granted for this company project to be generalized and publicized*

## Project Background
An established B2B dental wholesaler processes thousands of transactions monthly through its regional sales teams. While the company maintained extensive records within QuickBooks, this historical data remained significantly underutilized for proactive sales strategy. This project synthesized years of transaction data to build a predictive ecosystem that identifies critical cross-sell opportunities, directly improving Sintco's commercial outreach and average order value (AOV).

## The Business Challenge
In the dental supply industry, sales representatives must navigate complex product catalogs and understand nuanced clinical workflows.
1. **Missed Opportunities:** Reps often missed complementary product sales (ex. selling a high-end resin cement but forgetting to pitch the required etching gel and mixing tips).
2. **Data Silos:** Valuable purchasing history was locked inside accounting software (QuickBooks), making it inaccessible for proactive sales strategy.
3. **The "Black Box" Problem:** Even when standard data reports were available, sales teams hesitated to use them because they lacked context. A simple list of recommended products without reasoning is difficult for a rep to pitch confidently to a clinic.

## The Solution
We developed the **Dental Product Recommendation System**, a predictive analytics platform built specifically for non-technical sales users.

Rather than just building a mathematical model, we developed a complete product suite:
* **The Intelligence Engine:** An automated data pipeline extracts raw transaction data, cleans it using modern data warehousing techniques (dbt), and trains a Collaborative Filtering Machine Learning model. The model learns the hidden relationships between products based on the purchasing habits of hundreds of clinics.
* **The Contextual Dashboard:** A custom web application gives sales reps instant access to AI predictions. Crucially, the UI displays the clinic's historical top purchases *alongside* the AI recommendations. This provides the "Why", allowing the rep to see that because Clinic A buys high volumes of *Xylocaine*, they are highly likely to need *Astracaine*.

<img width="800" height="769" alt="preview" src="https://github.com/user-attachments/assets/bb8f0b83-1e70-4913-9753-ed5ab8675333" />

## Data Architecture & Pipeline
The Dental Product Recommendation system was built on a modern Medallion architecture, ensuring that raw accounting data is cleaned, transformed, and served with zero manual intervention. The entire stack is containerized to allow for Single-Click updates.

### 1) Data Structure & Schema
The core database consists of a high-density transaction matrix with a total row count exceeding 100,000 records.

| Columns | Type | Description |
| :--- | :--- | :--- |
| **clinic_id** | Integer | Unique identifier for the dental practice |
| **clinic_name** | String | Human-readable name (Formatted to Title Case) |
| **item_code** | String | Unique SKU for dental products |
| **item_description** | String | Human-readable product name |
| **purchase_count** | Integer | Frequency of purchase for procedural weighting |

### 2. Automated Pipeline
1.  **Ingestion:** A custom Python ETL (Extract, Transform, Load) engine extracts raw QuickBooks CSVs and loads them into a **PostgreSQL** instance managed by **Docker**.
2.  **Transformation (dbt):** The **Data Build Tool (dbt)** performs quality checks and organizes raw data into a "Golden" staging table, removing duplicates and correcting SKU inconsistencies.
3.  **ML Inference:** The system triggers a **Collaborative Filtering (ALS)** training script, generating a compressed mathematical model (`.npz`) and a locked sparse matrix to prevent ID drift.
4.  **Serving:** A **FastAPI** backend loads the model into RAM for sub-millisecond inference, serving results to a **Streamlit** dashboard.

## Value Delivered & Key Innovations

**1. Clinical Workflow Recognition**
The AI successfully learned dental procedures without being explicitly programmed. It accurately predicts prerequisites—such as recommending specific burs and etchants to clinics that recently purchased permanent crowns—enabling reps to sell complete procedural kits rather than isolated items.

**2. Accountant-Proof Deployment**
To ensure adoption, the entire complex software architecture was containerized. The system features a one-click setup that automatically builds the database, trains the AI on fresh data, and launches the dashboard, allowing non-technical staff to update the system at the end of the month without engineering support.

**3. Zero-Latency User Experience**
Sales reps need answers while on the phone with clients. By decoupling the machine learning math from the user interface and serving the model entirely from RAM via a dedicated API, the dashboard returns complex AI predictions in milliseconds.

## Technical Architecture Overview
* **Data Layer:** PostgreSQL (Containerized), dbt (Data Build Tool)
* **Machine Learning:** Python, Implicit (ALS Algorithm), MLflow
* **Serving Layer:** FastAPI (REST API)
* **Presentation Layer:** Streamlit