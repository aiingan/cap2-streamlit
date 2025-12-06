import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, inspect
import plotly.express as px
import google.generativeai as genai

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Cinema Analytics Capstone", layout="wide", page_icon="🎬")
st.title("🎬 Hệ Thống Phân Tích Doanh Thu & GenAI")
st.markdown("*Capstone Project - ETL Pipeline & AI Integration*")

# 2. HÀM KẾT NỐI DATABASE
@st.cache_resource
def get_connection():
    return create_engine(st.secrets["DB_URL"])

# 3. LOAD DỮ LIỆU TỰ ĐỘNG (Tự dò tên bảng)
@st.cache_data
def load_data():
    engine = get_connection()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        return None, "Không tìm thấy bảng nào trong Database!"
    
    # Ưu tiên lấy bảng đầu tiên tìm thấy
    table_name = tables[0] 
    query = f"SELECT * FROM {table_name} LIMIT 2000"
    df = pd.read_sql(query, engine)
    return df, None

try:
    df, error = load_data()
    if error:
        st.error(error)
        st.stop()
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# 4. GIAO DIỆN CHÍNH
tab1, tab2 = st.tabs(["📊 Dashboard Báo Cáo", "🤖 Trợ lý AI"])

with tab1:
    st.header("Tổng quan thị trường")
    
    # KPI Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số phim", f"{len(df):,}")
    
    # Tự động tìm cột để hiện KPI
    num_cols = df.select_dtypes(include=['number']).columns
    if 'revenue' in num_cols:
         c2.metric("Tổng Doanh Thu", f"${df['revenue'].sum():,.0f}")
    if 'vote_average' in df.columns:
         c3.metric("Điểm đánh giá TB", f"{df['vote_average'].mean():.2f}")
    elif 'rating' in df.columns:
         c3.metric("Điểm đánh giá TB", f"{df['rating'].mean():.2f}")

    st.divider()
    
    # Biểu đồ
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Phân bố điểm đánh giá")
        rating_col = 'vote_average' if 'vote_average' in df.columns else ('rating' if 'rating' in df.columns else None)
        if rating_col:
            fig1 = px.histogram(df, x=rating_col, nbins=20, title="Phổ điểm phim")
            st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        st.subheader("Top Phim Doanh thu cao nhất")
        rev_col = 'revenue' if 'revenue' in df.columns else None
        title_col = 'title' if 'title' in df.columns else ('original_title' if 'original_title' in df.columns else None)
        
        if rev_col and title_col:
            top_df = df.nlargest(10, rev_col)
            fig2 = px.bar(top_df, y=title_col, x=rev_col, orientation='h')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Dữ liệu thiếu cột Doanh thu (revenue) hoặc Tên phim (title) để vẽ biểu đồ này.")

    with st.expander("Xem dữ liệu chi tiết"):
        st.dataframe(df)

with tab2:
    st.header("Chat với dữ liệu (GenAI)")
    
    # KIỂM TRA API KEY
    if "GEMINI_API_KEY" in st.secrets:
        # Cấu hình AI
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # --- CHỐT MODEL TỪ DANH SÁCH BẠN GỬI ---
        model = genai.GenerativeModel('models/gemini-2.0-flash') 
        
        # Giao diện Chat
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Hỏi gì đó (VD: Phim nào doanh thu cao nhất? Xu hướng là gì?)"):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Xử lý trả lời
            try:
                # Gửi data mẫu (5 dòng) để AI hiểu ngữ cảnh
                data_context = df.head(5).to_string()
                full_prompt = f"Bạn là chuyên gia dữ liệu phim. Dựa vào mẫu dữ liệu này:\n{data_context}\n\nHãy trả lời câu hỏi: {prompt}"
                
                response = model.generate_content(full_prompt)
                bot_reply = response.text
                
                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
            except Exception as e:
                st.error(f"
