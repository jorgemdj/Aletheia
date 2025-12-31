import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Mentor de Diário 2026", layout="wide")

st.title("🧠 Mentor de Diário 2026")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar para métricas
with st.sidebar:
    st.header("📊 Dashboard Rápido")
    # Aqui poderíamos buscar do DB, mas usaremos a última resposta da sessão para o MVP
    if "last_metrics" in st.session_state:
        m = st.session_state.last_metrics
        st.metric("Água (ml)", m.get('agua', 0))
        st.metric("Sono (h)", m.get('sono', 0))
    
    if st.button("Gerar Retrospectiva"):
        res = requests.get("http://localhost:8000/review-semanal").json()
        with st.expander("📅 Insight da Semana", expanded=True):
            st.markdown(res['markdown'])

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Como foi seu dia hoje?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = requests.post("http://localhost:8000/registrar", json={"texto": prompt}).json()
        st.markdown(response["resposta"])
        st.session_state.last_metrics = response["metrics"]
        st.session_state.messages.append({"role": "assistant", "content": response["resposta"]})