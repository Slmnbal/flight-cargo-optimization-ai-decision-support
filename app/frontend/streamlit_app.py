"""
Basit karar destek arayüzü. Backend'in (uvicorn app.main:app) çalıştığını varsayar.
Çalıştırmak için: streamlit run streamlit_app.py
"""
import os

import pandas as pd
import requests
import streamlit as st

# Yerelde çalıştırınca (streamlit run) varsayılan localhost'u kullanır.
# Docker Compose içinde çalışınca, backend'e "localhost" ile değil servis adıyla
# ("backend") erişilir - bunu docker-compose.yml içindeki API_URL ortam değişkeni
# ile override edeceğiz. Kod tek satır değişmeden iki ortamda da çalışır.
API_URL = os.getenv("API_URL", "http://localhost:8000")

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
    st.caption(
        "Örnek: 'default senaryosunda kabul edilen talepler neler?' (canlı veri) ya da "
        "'priority_class nasıl işliyor?' (dokümantasyon/RAG). Sohbet aynı oturum boyunca "
        "hafızasını korur -- 'az önce bahsettiğin talep' gibi takip soruları sorabilirsin."
    )

    if "agent_session_id" not in st.session_state:
        st.session_state["agent_session_id"] = None
    if "agent_chat_history" not in st.session_state:
        st.session_state["agent_chat_history"] = []

    for turn in st.session_state["agent_chat_history"]:
        st.chat_message(turn["role"]).write(turn["content"])

    question = st.chat_input("Sorunu yaz")
    if question:
        st.chat_message("user").write(question)
        ask_resp = requests.post(
            f"{API_URL}/agent/ask",
            json={"question": question, "session_id": st.session_state["agent_session_id"]},
        )
        if ask_resp.ok:
            data = ask_resp.json()
            st.session_state["agent_session_id"] = data["session_id"]
            st.session_state["agent_chat_history"].append({"role": "user", "content": question})
            st.session_state["agent_chat_history"].append({"role": "assistant", "content": data["answer"]})
            st.chat_message("assistant").write(data["answer"])
        else:
            st.error(f"Hata: {ask_resp.text}")

    if st.session_state["agent_chat_history"] and st.button("Sohbeti sıfırla"):
        st.session_state["agent_session_id"] = None
        st.session_state["agent_chat_history"] = []
        st.rerun()
else:
    st.warning("Backend'e ulaşılamadı. `uvicorn app.main:app --reload` ile çalıştığından emin ol.")
