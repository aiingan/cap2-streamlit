import streamlit as st
from db import get_engine
from etl import run_etl
from genai import ask_genai

st.title("ETL + GenAI Capstone")

engine = get_engine()

upload = st.file_uploader("Upload file CSV", type=["csv"])

if upload:
    df = run_etl(upload, engine)
    st.success("ETL thành công!")
    st.dataframe(df)

prompt = st.text_input("Hỏi GenAI hoặc hỏi dữ liệu:")
if prompt:
    answer = ask_genai(prompt)
    st.write(answer)
