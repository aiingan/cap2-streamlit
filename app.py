import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import google.generativeai as genai

# 1. CẤU HÌNH TRANG WEB
st.set_page_config(page_title="Phim Dashboard & AI", layout="wide", page_icon="🎬")

st.title("🎬 Hệ Thống Phân Tích Doanh Thu Phim & GenAI")
st.markdown("Capstone Project: Tích hợp ETL pipeline trên Cloud và Trợ lý ảo AI")

# 2. KẾT NỐI DATABASE (NEON)
@st.cache_resource
def get_database_connection():
    # Lấy secret từ Streamlit Cloud
    db_url = st.secrets["DB_URL"]
    return create_engine(db_url)

try:
    engine = get_database_connection()
    # Test kết nối bằng cách lấy dữ liệu
    # LƯU Ý: Đổi 'movies_fact' thành tên bảng thật của bạn trong Neon (ví dụ: film_ratings, movies...)
    query = "SELECT * FROM film_ratings LIMIT 2000" 
    df = pd.read_sql(query, engine)
    
except Exception as e:
    st.error(f"⚠️ Lỗi kết nối Database: {e}")
    st.stop()

# 3. DASHBOARD BÁO CÁO (Yêu cầu: Bảng + Chart)
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Phân Tích", "🤖 Chatbot AI", "fw Dữ liệu chi tiết"])

with tab1:
    st.header("Tổng quan thị trường phim")
    
    # KPI Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số phim khảo sát", f"{len(df):,}")
    
    # Kiểm tra xem có cột 'rating' hay 'vote_average' không để hiển thị
    rating_col = 'rating' if 'rating' in df.columns else 'vote_average'
    if rating_col in df.columns:
        col2.metric("Điểm đánh giá trung bình", f"{df[rating_col].mean():.2f}/5")
    
    st.divider()
    
    # Biểu đồ 1: Phân bố điểm đánh giá
    if rating_col in df.columns:
        st.subheader("Phân bố điểm đánh giá của khán giả")
        fig_hist = px.histogram(df, x=rating_col, nbins=20, title="Số lượng phim theo mức điểm", color_discrete_sequence=['#FF4B4B'])
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Biểu đồ 2: Top phim (Ví dụ theo Rating)
    if 'title' in df.columns and rating_col in df.columns:
        st.subheader("Top 10 Phim được đánh giá cao nhất")
        top_movies = df.nlargest(10, rating_col)
        fig_bar = px.bar(top_movies, x=rating_col, y='title', orientation='h', title="Top Rated Movies")
        st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.header("Trợ lý ảo phân tích phim (GenAI)")
    st.info("💡 Tính năng này giúp tra cứu thông tin phim thông qua Gemini AI.")
    
    # Kiểm tra API Key
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Giao diện chat
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Hỏi về dữ liệu phim (VD: Phim nào hay nhất? Xu hướng phim hiện nay?)"):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Kỹ thuật RAG đơn giản: Gửi kèm data mẫu cho AI
            data_context = df.head(10).to_string()
            full_prompt = f"Bạn là chuyên gia phân tích phim. Dựa vào dữ liệu mẫu sau: \n{data_context}\n. Hãy trả lời câu hỏi: {prompt}"
            
            try:
                response = model.generate_content(full_prompt)
                bot_reply = response.text
                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            except Exception as e:
                st.error(f"Lỗi gọi AI: {e}")
    else:
        st.warning("⚠️ Chưa cấu hình GEMINI_API_KEY trong Secrets của Streamlit Cloud.")

with tab3:
    st.subheader("Dữ liệu thô từ Neon Database")
    st.dataframe(df)
