import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import google.generativeai as genai

st.set_page_config(page_title="Phim Dashboard", layout="wide")
st.title("🎬 Hệ Thống Phân Tích Phim & GenAI")

# --- KẾT NỐI DATABASE ---
try:
    engine = create_engine(st.secrets["DB_URL"])
    # Nhớ sửa 'movies_fact' thành tên bảng thật của bạn nếu khác
    df = pd.read_sql("SELECT * FROM movies_fact LIMIT 1000", engine)
except Exception as e:
    st.error(f"Lỗi DB: {e}")
    st.stop()

# --- GIAO DIỆN ---
tab1, tab2 = st.tabs(["📊 Biểu đồ", "🤖 Chatbot"])

with tab1:
    st.write("Dữ liệu phim:")
    st.dataframe(df.head())

with tab2:
    st.header("Chat với AI")
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Dùng model này
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        query = st.text_input("Hỏi về phim:")
        if query:
            try:
                # Gửi data mẫu + câu hỏi
                context = df.head(5).to_string()
                prompt = f"Dữ liệu: {context}\n Câu hỏi: {query}"
                response = model.generate_content(prompt)
                st.write(response.text)
            except Exception as e:
                st.error(f"Lỗi AI: {e}")
    else:
        st.warning("Thiếu API Key")
