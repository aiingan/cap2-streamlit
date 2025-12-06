import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import google.generativeai as genai

# 1. CẤU HÌNH
st.set_page_config(page_title="Cinema Analytics Capstone", layout="wide", page_icon="🎬")
st.title("🎬 Hệ Thống Phân Tích Doanh Thu & GenAI")

# 2. KẾT NỐI
@st.cache_resource
def get_connection():
    return create_engine(st.secrets["DB_URL"])

# Cấu hình tên bảng (Sửa nếu cần)
current_table = "ratings"

# --- HÀM CHUẨN HÓA TÊN CỘT (FIX LỖI) ---
def clean_columns(df):
    # Đổi hết về chữ thường và bỏ khoảng trắng thừa
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    return df

# 3. LOAD DATA
@st.cache_data
def load_data():
    try:
        engine = get_connection()
        query = f"SELECT * FROM {current_table} LIMIT 10000"
        df = pd.read_sql(query, engine)
        df = clean_columns(df) # <--- Bước quan trọng: Chuẩn hóa tên cột
        return df
    except Exception as e:
        return None

df = load_data()

# --- SIDEBAR UPLOAD ---
with st.sidebar:
    st.header("📥 Nạp dữ liệu")
    up_file = st.file_uploader("Upload CSV", type=["csv"])
    if up_file and st.button("Lưu"):
        try:
            new_df = pd.read_csv(up_file)
            new_df = clean_columns(new_df) # Chuẩn hóa trước khi lưu
            new_df.to_sql(current_table, get_connection(), if_exists='append', index=False)
            st.success("Đã lưu!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi: {e}")

if df is None:
    st.error(f"Không đọc được bảng '{current_table}'.")
    st.stop()

# 4. DASHBOARD
tab1, tab2 = st.tabs(["📊 Báo Cáo", "🤖 Chatbot"])

with tab1:
    st.header("Tổng quan")
    
    # --- DEBUG: HIỆN TÊN CỘT ĐỂ KIỂM TRA ---
    with st.expander("🔍 Kiểm tra tên cột (Bấm vào đây nếu biểu đồ lỗi)"):
        st.write("Danh sách cột trong dữ liệu của bạn:", list(df.columns))
        if 'revenue' not in df.columns:
            st.error("❌ Cảnh báo: Dữ liệu này KHÔNG CÓ cột 'revenue' (doanh thu). Biểu đồ doanh thu sẽ không vẽ được.")

    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng phim", len(df))
    
    # Tự động tìm cột
    score_col = 'vote_average' if 'vote_average' in df.columns else ('rating' if 'rating' in df.columns else None)
    rev_col = 'revenue' if 'revenue' in df.columns else None
    title_col = 'title' if 'title' in df.columns else ('original_title' if 'original_title' in df.columns else None)

    if score_col: c2.metric("Điểm TB", round(df[score_col].mean(), 2))
    if rev_col: c3.metric("Tổng Doanh Thu", f"${df[rev_col].sum():,.0f}")
    
    st.divider()

    # BIỂU ĐỒ
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Phân bố điểm")
        if score_col:
            st.plotly_chart(px.histogram(df, x=score_col, nbins=20), use_container_width=True)
        else:
            st.warning("⚠️ Thiếu cột điểm số (rating/vote_average)")

    with col2:
        st.subheader("Top 10 Rating")
        if score_col and title_col:
            top_rate = df.nlargest(10, score_col).sort_values(score_col)
            st.plotly_chart(px.bar(top_rate, y=title_col, x=score_col, orientation='h'), use_container_width=True)

    # BIỂU ĐỒ DOANH THU (Cái bạn đang cần)
    st.subheader("Top 10 Doanh Thu")
    if rev_col and title_col:
        top_rev = df.nlargest(10, rev_col).sort_values(rev_col)
        st.plotly_chart(px.bar(top_rev, y=title_col, x=rev_col, orientation='h', color=rev_col), use_container_width=True)
    else:
        st.error("⚠️ KHÔNG VẼ ĐƯỢC: Dữ liệu thiếu cột 'revenue' hoặc 'title'. Hãy xem mục 'Kiểm tra tên cột' ở trên.")

with tab2:
    st.header("Chatbot AI")
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        if prompt := st.chat_input("Hỏi gì đó..."):
            with st.chat_message("user"): st.write(prompt)
            try:
                context = df.head(5).to_string()
                resp = model.generate_content(f"Data:\n{context}\nQ: {prompt}")
                with st.chat_message("assistant"): st.write(resp.text)
            except Exception as e: st.error(str(e))
