import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import google.generativeai as genai

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Cinema Analytics Capstone", layout="wide", page_icon="🎬")
st.title("🎬 Hệ Thống Phân Tích Doanh Thu & GenAI")
st.markdown("*Capstone Project - ETL Pipeline & AI Integration*")

# 2. KẾT NỐI DATABASE
@st.cache_resource
def get_connection():
    return create_engine(st.secrets["DB_URL"])

# --- SỬA Ở ĐÂY: KHÔNG DÙNG TỰ DÒ NỮA ---
# Thay 'movies_fact' bằng tên bảng thật chứa 45k dòng trên Neon của bạn
current_table = "ratings" 

# --- SIDEBAR: UPLOAD DỮ LIỆU ---
with st.sidebar:
    st.header("📥 Nạp dữ liệu mới")
    uploaded_file = st.file_uploader("Chọn file CSV phim mới", type=["csv"])
    
    if uploaded_file is not None:
        if st.button("Lưu vào Database"):
            try:
                df_new = pd.read_csv(uploaded_file)
                # Load vào đúng bảng current_table
                df_new.to_sql(current_table, get_connection(), if_exists='append', index=False)
                st.success(f"✅ Đã thêm {len(df_new)} dòng vào bảng '{current_table}'!")
                st.cache_data.clear() 
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi Upload: {e}")

# 3. LOAD DỮ LIỆU
@st.cache_data
def load_data():
    engine = get_connection()
    # Tăng limit lên 10000 để xem cho đã
    query = f"SELECT * FROM {current_table} LIMIT 10000"
    df = pd.read_sql(query, engine)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Lỗi đọc bảng '{current_table}': {e}. Hãy kiểm tra lại tên bảng trên Neon!")
    st.stop()

# 4. GIAO DIỆN DASHBOARD
tab1, tab2 = st.tabs(["📊 Báo Cáo & Biểu Đồ", "🤖 Trợ lý AI"])

with tab1:
    st.header(f"Dữ liệu từ bảng: {current_table}")
    
    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số phim", f"{len(df):,}")
    
    if 'revenue' in df.columns:
         c2.metric("Tổng Doanh Thu", f"${df['revenue'].sum():,.0f}")
    
    rating_col = 'vote_average' if 'vote_average' in df.columns else ('rating' if 'rating' in df.columns else None)
    if rating_col:
         c3.metric("Điểm đánh giá TB", f"{df[rating_col].mean():.2f}")

    st.divider()
    
    # Chart
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Phân bố điểm đánh giá")
        if rating_col:
            fig1 = px.histogram(df, x=rating_col, nbins=20)
            st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        st.subheader("Top Doanh Thu")
        rev_col = 'revenue' if 'revenue' in df.columns else None
        title_col = 'title' if 'title' in df.columns else ('original_title' if 'original_title' in df.columns else None)
        if rev_col and title_col:
            top_df = df.nlargest(10, rev_col)
            fig2 = px.bar(top_df, y=title_col, x=rev_col, orientation='h')
            st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Xem dữ liệu chi tiết"):
        st.dataframe(df)

with tab2:
    st.header("Chatbot AI")
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Hỏi về phim..."):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                # Lấy mẫu 5 dòng
                data_context = df.head(5).to_string()
                full_prompt = f"Data:\n{data_context}\nQ: {prompt}"
                response = model.generate_content(full_prompt)
                st.chat_message("assistant").markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Lỗi AI: {e}")
