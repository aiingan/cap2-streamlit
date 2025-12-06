import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import google.generativeai as genai

# --- 1. CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Phim Analytics & AI", layout="wide", page_icon="🎬")
st.title("🎬 Hệ Thống Phân Tích Phim & Chatbot GenAI")
st.markdown("*Capstone Project - ETL Pipeline & AI Integration*")

# --- THÊM VÀO APP.PY ---

# TẠO SIDEBAR UPLOAD
with st.sidebar:
    st.header("📥 Nạp dữ liệu mới")
    uploaded_file = st.file_uploader("Chọn file CSV phim mới", type=["csv"])
    
    if uploaded_file is not None:
        if st.button("Lưu vào Database"):
            try:
                # Đọc file upload
                df_new = pd.read_csv(uploaded_file)
                # Đổi tên cột cho giống Database (nếu cần) - Bước Transform
                # df_new.columns = [c.lower().replace(' ', '_') for c in df_new.columns]
                
                # Load vào Neon
                df_new.to_sql('movies_fact', engine, if_exists='append', index=False)
                st.success(f"✅ Đã thêm {len(df_new)} dòng dữ liệu!")
                st.cache_data.clear() # Xóa cache để Web cập nhật số liệu mới
            except Exception as e:
                st.error(f"Lỗi: {e}")

# --- 2. KẾT NỐI NEON DATABASE ---
@st.cache_resource
def get_connection():
    # Lấy link kết nối từ Secrets
    return create_engine(st.secrets["DB_URL"])

try:
    engine = get_connection()
    # LƯU Ý: Nếu bảng của bạn tên khác 'ratings', hãy sửa dòng dưới
    # Query lấy dữ liệu mẫu
    df = pd.read_sql("SELECT * FROM ratings LIMIT 1000", engine)
except Exception as e:
    st.error(f"❌ Lỗi kết nối: {e}")
    st.stop()

# --- 3. GIAO DIỆN CHÍNH (TABS) ---
tab1, tab2 = st.tabs(["📊 Báo Cáo & Biểu Đồ", "🤖 Chatbot AI"])

with tab1:
    st.header("Tổng quan dữ liệu")
    
    # KPI (Chỉ số chính)
    c1, c2 = st.columns(2)
    c1.metric("Tổng số phim", f"{len(df):,}")
    
    # Kiểm tra cột để hiện KPI
    if 'rating' in df.columns:
        c2.metric("Điểm đánh giá TB", f"{df['rating'].mean():.1f} / 5.0")
    elif 'vote_average' in df.columns:
        c2.metric("Điểm đánh giá TB", f"{df['vote_average'].mean():.1f} / 10.0")

    st.divider()
    
    # Vẽ biểu đồ (Chia 2 cột)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Phân bố điểm đánh giá")
        # Tìm cột điểm số
        score_col = 'rating' if 'rating' in df.columns else 'vote_average'
        if score_col in df.columns:
            fig1 = px.histogram(df, x=score_col, nbins=20, title="Tần suất điểm số")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("Không tìm thấy cột điểm số (rating/vote_average)")

    with col_chart2:
        st.subheader("Top phim (theo data mẫu)")
        # Tìm cột tên phim
        title_col = 'title' if 'title' in df.columns else 'original_title'
        if title_col in df.columns and score_col in df.columns:
            top_df = df.nlargest(10, score_col)
            fig2 = px.bar(top_df, y=title_col, x=score_col, orientation='h', title="Top 10 Phim")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Thiếu cột tên phim hoặc điểm số")

    with st.expander("Xem dữ liệu chi tiết (Bảng)"):
        st.dataframe(df)

with tab2:
    st.header("Trợ lý ảo thông minh")
    
    # Kiểm tra Key Gemini
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Input câu hỏi
        user_query = st.text_input("Hỏi gì đó về phim (VD: Phim nào hay nhất trong danh sách?)")
        
        if user_query:
            with st.spinner("AI đang suy nghĩ..."):
                try:
                    # Gửi data mẫu + câu hỏi cho AI
                    model = genai.GenerativeModel('models/gemini-2.0-flash')
                    data_str = df.head(10).to_string()
                    prompt = f"Dựa vào dữ liệu này:\n{data_str}\n\nHãy trả lời: {user_query}"
                    
                    response = model.generate_content(prompt)
                    st.success("AI trả lời:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")
    else:
        st.warning("⚠️ Bạn chưa nhập GEMINI_API_KEY vào Secrets trên Streamlit Cloud!")
