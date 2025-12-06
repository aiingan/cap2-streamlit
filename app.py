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

# 3. XÁC ĐỊNH TÊN BẢNG TỰ ĐỘNG
# Hàm này giúp tìm xem bảng tên là 'movies_fact' hay 'ratings' để code không bị lỗi
def get_table_name():
    engine = get_connection()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if tables:
        return tables[0] # Lấy bảng đầu tiên tìm thấy
    return "movies_fact" # Tên mặc định nếu không tìm thấy

current_table = get_table_name()

# --- SIDEBAR: UPLOAD DỮ LIỆU (Code bạn yêu cầu thêm) ---
with st.sidebar:
    st.header("📥 Nạp dữ liệu mới")
    uploaded_file = st.file_uploader("Chọn file CSV phim mới", type=["csv"])
    
    if uploaded_file is not None:
        if st.button("Lưu vào Database"):
            try:
                # Đọc file upload
                df_new = pd.read_csv(uploaded_file)
                
                # Load vào Neon (Dùng đúng tên bảng đã dò được)
                engine = get_connection()
                df_new.to_sql(current_table, engine, if_exists='append', index=False)
                
                st.success(f"✅ Đã thêm {len(df_new)} dòng vào bảng '{current_table}'!")
                st.cache_data.clear() # Xóa cache để biểu đồ tự cập nhật
                st.rerun() # Load lại trang ngay lập tức
            except Exception as e:
                st.error(f"Lỗi Upload: {e}")

# 4. LOAD DỮ LIỆU CHO DASHBOARD
@st.cache_data
def load_data(table_name):
    engine = get_connection()
    query = f"SELECT * FROM {table_name} LIMIT 3000"
    df = pd.read_sql(query, engine)
    return df

try:
    df = load_data(current_table)
except Exception as e:
    st.error(f"Lỗi đọc dữ liệu: {e}")
    st.stop()

# 5. GIAO DIỆN CHÍNH (TABS)
tab1, tab2 = st.tabs(["📊 Báo Cáo & Biểu Đồ", "🤖 Trợ lý AI"])

with tab1:
    st.header(f"Tổng quan dữ liệu (Bảng: {current_table})")
    
    # KPI Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng số phim", f"{len(df):,}")
    
    # Tự động tìm cột phù hợp để hiện KPI
    if 'revenue' in df.columns:
         c2.metric("Tổng Doanh Thu", f"${df['revenue'].sum():,.0f}")
    
    rating_col = 'vote_average' if 'vote_average' in df.columns else ('rating' if 'rating' in df.columns else None)
    if rating_col:
         c3.metric("Điểm đánh giá TB", f"{df[rating_col].mean():.2f}")

    st.divider()
    
    # Vẽ biểu đồ
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Phân bố điểm đánh giá")
        if rating_col:
            fig1 = px.histogram(df, x=rating_col, nbins=20, title="Phổ điểm phim", color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Chưa có cột điểm số để vẽ biểu đồ.")
    
    with col_chart2:
        st.subheader("Top Phim Doanh thu cao nhất")
        rev_col = 'revenue' if 'revenue' in df.columns else None
        title_col = 'title' if 'title' in df.columns else ('original_title' if 'original_title' in df.columns else None)
        
        if rev_col and title_col:
            top_df = df.nlargest(10, rev_col)
            fig2 = px.bar(top_df, y=title_col, x=rev_col, orientation='h', title="Top Doanh Thu")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Thiếu cột Doanh thu hoặc Tên phim để vẽ biểu đồ này.")

    with st.expander("Xem dữ liệu chi tiết"):
        st.dataframe(df)

with tab2:
    st.header("Chat với dữ liệu (GenAI)")
    
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Dùng Model chuẩn mà tài khoản bạn hỗ trợ
        model = genai.GenerativeModel('models/gemini-2.0-flash') 
        
        # Hiển thị lịch sử chat
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input
        if prompt := st.chat_input("Hỏi gì đó về phim?"):
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                # Gửi data mẫu cho AI
                data_context = df.head(5).to_string()
                full_prompt = f"Data mẫu:\n{data_context}\n\nCâu hỏi: {prompt}"
                
                response = model.generate_content(full_prompt)
                bot_reply = response.text
                
                with st.chat_message("assistant"):
                    st.markdown(bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            except Exception as e:
                st.error(f"Lỗi AI: {e}")
    else:
        st.warning("⚠️ Chưa nhập GEMINI_API_KEY trong Secrets!")
