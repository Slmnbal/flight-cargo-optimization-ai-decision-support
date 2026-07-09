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

    st.divider()
    st.subheader("ML: Kabul Olasılığı Tahmini")

    ml_col1, ml_col2 = st.columns(2)
    with ml_col1:
        if st.button("ML Modelini Eğit"):
            train_resp = requests.post(f"{API_URL}/ml/train")
            if train_resp.ok:
                st.session_state["train_info"] = train_resp.json()
            else:
                st.error(f"Hata: {train_resp.text}")

    if "train_info" in st.session_state:
        info = st.session_state["train_info"]
        if info["trained"]:
            st.success(f"Model eğitildi. Doğruluk (accuracy): {info['accuracy']:.2f} ({info['n_samples']} örnek)")
        else:
            st.warning(info["detail"])

    with ml_col2:
        if not df.empty:
            selected_id = st.selectbox("Kabul olasılığını görmek istediğin request_id", df["request_id"].tolist())
            if st.button("Olasılığı Göster"):
                pred_resp = requests.get(f"{API_URL}/ml/predict/{selected_id}")
                if pred_resp.ok:
                    prob = pred_resp.json()["acceptance_probability"]
                    st.info(f"Talep #{selected_id} için tahmini kabul olasılığı: %{prob * 100:.1f}")
                else:
                    st.error(f"Hata: {pred_resp.text}")
    st.divider()
    st.subheader("AI Agent'a Soru Sor")
    st.caption("Örnek: 'default senaryosunda kabul edilen talepler neler?' ya da '1 numaralı talep neden reddedildi?'")

    question = st.text_input("Sorunu yaz")
    if st.button("Sor"):
        ask_resp = requests.post(f"{API_URL}/agent/ask", json={"question": question})
        if ask_resp.ok:
            st.info(ask_resp.json()["answer"])
        else:
            st.error(f"Hata: {ask_resp.text}")
else:
    st.warning("Backend'e ulaşılamadı. `uvicorn app.main:app --reload` ile çalıştığından emin ol.")
