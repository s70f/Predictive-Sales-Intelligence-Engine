import streamlit as st
import requests
import pandas as pd


def get_recommendations(clinic_id):
    response = requests.get(f"http://localhost:8000/recommend/{clinic_id}")

    if response.status_code == 200:
        return response.json()
    else:
        return None


st.set_page_config(page_title="Dental AI", page_icon="🦷")
st.title("Product Recommender Dashboard")
st.write("Professional Sales Support Tool")

api_base = "http://localhost:8000"


# Fetching the products one time
@st.cache_data
def fetch_clinics():
    try:
        response = requests.get(f"{api_base}/clinics")
        return response.json()
    except:
        return []


clinics = fetch_clinics()

if not clinics:
    st.error("Could not connect to FastAPI. Please make sure uvicorn is running.")
    st.stop()


# Pick Clinic Name
selected_name = st.selectbox("Start typing a clinic name", options=clinics)

clinic_id = clinics.index(selected_name)

# 4. The Action Button
if st.button("Analyze Clinic"):
    with st.spinner(f"Analyzing {selected_name}"):

        # Ping BOTH endpoints at the same time
        rec_res = requests.get(f"{api_base}/recommend/{clinic_id}")
        hist_res = requests.get(f"{api_base}/history/{clinic_id}")

        if rec_res.status_code == 200 and hist_res.status_code == 200:
            rec_data = rec_res.json()
            hist_data = hist_res.json()

            st.success(f"Analysis Complete for **{selected_name}**")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Top Purchase History")
                if hist_data['history']:
                    hist_df = pd.DataFrame(hist_data['history'])

                    # Select only the human-friendly name and count
                    display_hist = hist_df[["Product Name", "Times Purchased"]]

                    # SWITCH: Use st.table for a clean, full-width look
                    st.table(display_hist)
                else:
                    st.info("No purchase history found.")

            with col2:
                st.subheader("AI Recommendations")

                rec_df = pd.DataFrame(rec_data['recommendations'])

                # Format the AI Confidence
                rec_df['score'] = rec_df['score'].apply(
                    lambda x: f"{x * 100:.1f}%")

                # Filter to show ONLY the Name and Match
                rec_df.columns = ["SKU", "Product Name", "AI Match"]
                display_rec = rec_df[["Product Name", "AI Match"]]

                # SWITCH: Use st.table to prevent cutting off long names
                st.table(display_rec)
        else:
            st.error(
                "API Error: Make sure FastAPI is running and both endpoints exist.")
