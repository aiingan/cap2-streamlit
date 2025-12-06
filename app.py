import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import google.generativeai as genai

# 1. CẤU HÌNH TRANG WEB
st.set_page_config(page_title="Cinema Analytics Capstone", layout="wide", page_icon="🎬")
st.title("🎬 Hệ Thống Phân Tích Doanh Thu & GenAI")
st.markdown("*Capstone Project - Dashboard & Chatbot*")

# 2. KẾT NỐI DATABASE
@st.cache_resource
def get_connection():
    return create_engine(st.secrets["DB_URL"])

# --- CẤU HÌNH TÊN BẢNG (Bạn sửa nếu cần) ---
current_table = "ratings"

# --- SIDEBAR: UPLOAD DỮ LIỆU ---
with st.sidebar:
    st.header("📥 Nạp dữ liệu mới")
    uploaded_file = st.file_uploader("Chọn file CSV phim mới", type=["csv"])
    if uploaded_file and st.button("Lưu vào Database"):
        try:
            df_new = pd.read_csv(uploaded_file)
            df_new.to_sql(current_table, get_connection(), if_exists='append', index=False)
            st.success(f"✅ Đã thêm {len(df_new)} dòng!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi Upload: {e}")

# 3. LOAD DỮ LIỆU
@st.cache_data
def load_data():
    engine = get_connection()
    try:
        # Lấy 10,000 dòng để phân tích cho chính xác
        query = f"SELECT * FROM {current_table} LIMIT 10000"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        return None

df = load_data()
if df is None:
    st.error(f"Lỗi: Không tìm thấy bảng '{current_table}'. Hãy kiểm tra tên bảng trên Neon!")
    st.stop()

# --- XÁC ĐỊNH TÊN CỘT CHUẨN (Để tránh lỗi cột) ---
# Cột tên phim
if 'title' in df.columns: title_col = 'title'
elif 'original_title' in df.columns: title_col = 'original_title'
else: title_col = None

# Cột điểm đánh giá
if 'vote_average' in df.columns: rating_col = 'vote_average'
elif 'rating' in df.columns: rating_col = 'rating'
else: rating_col = None

# Cột doanh thu
if 'revenue' in df.columns: rev_col = 'revenue'
else: rev_col = None


# 4. GIAO DIỆN CHÍNH
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Streamlit", "🤖 Chatbot AI", "📈 Tableau Public"])

with tab1:
    st.header("Tổng quan dữ liệu")

    # --- PHẦN 1: KPI TỔNG QUAN ---
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    # KPI 1: Tổng số phim
    col_kpi1.metric("Tổng số phim", f"{len(df):,}")

    # KPI 2: Điểm đánh giá trung bình
    if rating_col:
        avg_score = df[rating_col].mean()
        col_kpi2.metric("Điểm đánh giá TB", f"{avg_score:.2f} / 10")

    # KPI 3: Tổng doanh thu (nếu có)
    if rev_col:
        total_rev = df[rev_col].sum()
        col_kpi3.metric("Tổng Doanh Thu", f"${total_rev:,.0f}")

    st.divider()

    # --- PHẦN 2: PHÂN BỐ VÀ TOP RATING ---
    col_row2_1, col_row2_2 = st.columns(2)

    with col_row2_1:
        st.subheader("1. Phổ điểm phim (Phân bố)")
        if rating_col:
            # Histogram: Trục X là điểm, Trục Y là số lượng (Count)
            fig_hist = px.histogram(df, x=rating_col, nbins=20,
                                    labels={rating_col: "Điểm số"},
                                    color_discrete_sequence=['#3366CC'])
            fig_hist.update_layout(bargap=0.1)
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("Thiếu cột điểm đánh giá")

    with col_row2_2:
        st.subheader("2. Top 10 Phim hay nhất (Rating)")
        if rating_col and title_col:
            # Lấy top 10 theo điểm
            top_rating_df = df.nlargest(10, rating_col).sort_values(by=rating_col, ascending=True)
            fig_rate = px.bar(top_rating_df, y=title_col, x=rating_col, orientation='h',
                              labels={title_col: "Tên phim", rating_col: "Điểm"},
                              color=rating_col, color_continuous_scale='Viridis')
            st.plotly_chart(fig_rate, use_container_width=True)
        else:
            st.warning("Thiếu cột tên phim hoặc điểm")

    # --- PHẦN 3: TOP DOANH THU (Chạy hết chiều ngang) ---
    st.subheader("3. Top 10 Phim Doanh Thu Cao Nhất")
    if rev_col and title_col:
        # Lấy top 10 theo doanh thu
        top_rev_df = df.nlargest(10, rev_col).sort_values(by=rev_col, ascending=True)
        fig_rev = px.bar(top_rev_df, y=title_col, x=rev_col, orientation='h',
                         labels={title_col: "Tên phim", rev_col: "Doanh thu ($)"},
                         color=rev_col, color_continuous_scale='RdBu')
        st.plotly_chart(fig_rev, use_container_width=True)
    else:
        st.info("Dữ liệu không có cột Doanh thu (revenue) để vẽ biểu đồ này.")

    with st.expander("Xem dữ liệu chi tiết (Bảng)"):
        st.dataframe(df)


        # Nút Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Tải dữ liệu báo cáo (CSV)",
        data=csv,
        file_name='report_phim_capstone.csv',
        mime='text/csv',
    )

with tab2:
    st.header("Chatbot AI phân tích phim")
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('models/gemini-2.0-flash') # Model xịn

        if "messages" not in st.session_state: st.session_state.messages = []
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Hỏi về phim..."):
            st.chat_message("user").write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                # Kỹ thuật RAG: Gửi kèm data top 5 phim hay nhất để AI tham khảo
                top_data = df.nlargest(5, rating_col if rating_col else df.columns[0]).to_string()
                full_prompt = f"Dữ liệu Top 5 phim:\n{top_data}\n\nCâu hỏi: {prompt}"

                resp = model.generate_content(full_prompt)
                st.chat_message("assistant").write(resp.text)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
            except Exception as e:
                st.error(f"Lỗi AI: {e}")



with tab3:
    st.header("Báo cáo nâng cao từ Tableau")
    st.write("Dưới đây là báo cáo được tích hợp từ Tableau Public:")
    
    # Thay link bên dưới bằng Link Tableau thật của bạn
    tableau_url = "https://public.tableau.com/app/profile/t.ng.c.m.qu.nh/viz/Capstone_2_17650480549710/D5"
    
    # Code nhúng iframe
    st.markdown(f"""
        <iframe src="{tableau_url}" width="100%" height="800"></iframe>
    """, unsafe_allow_html=True)
