"""
Basit karar destek arayüzü. Backend'in (uvicorn app.main:app) çalıştığını varsayar.
Çalıştırmak için: streamlit run streamlit_app.py
"""
import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Flight Cargo Optimization", layout="wide")
st.title("Flight Cargo Optimization & AI Decision Support System")

col1, col2 = st.columns(2)
with col1:
    scenario_name = st.text_input("Senaryo adı", value="default")
with col2:
    if st.button("Optimizasyonu Çalıştır", type="primary"):
        resp = requests.post(f"{API_URL}/optimize", params={"scenario_name": scenario_name})
        if resp.ok:
            st.session_state["last_result"] = resp.json()
        else:
            st.error(f"Hata: {resp.text}")

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Solver Durumu", result["status"])
    k2.metric("Kabul Edilen", len(result["accepted"]))
    k3.metric("Reddedilen", len(result["rejected"]))
    k4.metric("Toplam Gelir", f"{result['total_revenue']:.0f}")

st.divider()

requests_resp = requests.get(f"{API_URL}/cargo-requests")
if requests_resp.ok:
    df = pd.DataFrame(requests_resp.json())
    st.subheader("Kargo Talepleri")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Backend'e ulaşılamadı. `uvicorn app.main:app --reload` ile çalıştığından emin ol.")
