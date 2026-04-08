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

if st.button("Generate AI Recommendations"):
    with st.spinner(f"Analyzing purchase history for {selected_name}..."):

        res = requests.get(f"{api_base}/recommend/{clinic_id}")

        if res.status_code == 200:
            data = res.json()

            st.success(
                f"Recommendations for **{selected_name}** (ID: {clinic_id})")

            rec_df = pd.DataFrame({
                "Product Code": data['recommendations'],
                "AI Confidence": data['scores']
            })

            # Display as a table
            st.table(rec_df)

            st.info(
                "These items are predicted based on similar clinics's purchasing patterns.")
        else:
            st.error("API Error: Could not generate recommendations.")
