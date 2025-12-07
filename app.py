import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import google.generativeai as genai
from PIL import Image
import io

# 1. CẤU HÌNH TRANG WEB
st.set_page_config(page_title="Cinema Analytics Capstone", layout="wide", page_icon="🎬")
st.title("🎬 Hệ Thống Phân Tích Doanh Thu & GenAI")
st.markdown("*Capstone Project - ETL Pipeline & AI Integration*")

# 2. KẾT NỐI DATABASE
@st.cache_resource
def get_connection():
    return create_engine(st.secrets["DB_URL"])

# --- CẤU HÌNH TÊN BẢNG ---
current_table = "ratings"

# --- HÀM HỖ TRỢ LƯU DỮ LIỆU (ETL) ---
def clean_and_save(df, source_name):
    try:
        # 1. Chuẩn hóa tên cột (về chữ thường, không dấu cách)
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        
        # 2. Lưu vào Neon
        df.to_sql(current_table, get_connection(), if_exists='append', index=False)
        
        # 3. Thông báo & Refresh
        st.success(f"✅ Đã nạp thành công {len(df)} dòng từ nguồn: {source_name}!")
        st.cache_data.clear() # Xóa cache để Dashboard cập nhật
        st.rerun()
    except Exception as e:
        st.error(f"❌ Lỗi khi lưu dữ liệu: {e}")

# --- SIDEBAR: TRUNG TÂM ETL (4 PHƯƠNG THỨC) ---
with st.sidebar:
    st.header("📥 Nạp dữ liệu đa nguồn")
    
    # Menu chọn phương thức nhập liệu
    input_method = st.selectbox(
        "Chọn phương thức input:",
        ["1. Upload File (CSV/Excel)", "2. Web Form (Nhập tay)", "3. Google Sheet API", "4. OCR Tài liệu (Ảnh/PDF)"]
    )
    st.divider()

    # --- MODE 1: UPLOAD FILE ---
    if input_method == "1. Upload File (CSV/Excel)":
        up_file = st.file_uploader("Chọn file dữ liệu", type=["csv", "xlsx"])
        if up_file and st.button("Lưu vào Database"):
            try:
                if up_file.name.endswith('.csv'):
                    df_new = pd.read_csv(up_file)
                else:
                    df_new = pd.read_excel(up_file)
                clean_and_save(df_new, "File Upload")
            except Exception as e: st.error(f"Lỗi đọc file: {e}")

    # --- MODE 2: WEB FORM (NHẬP TAY) ---
    elif input_method == "2. Web Form (Nhập tay)":
        with st.form("web_form_etl"):
            st.write("Nhập thông tin phim mới:")
            t_title = st.text_input("Tên phim (Title)")
            t_rev = st.number_input("Doanh thu ($)", min_value=0.0)
            t_vote = st.slider("Điểm đánh giá (0-10)", 0.0, 10.0, 5.0)
            
            submitted = st.form_submit_button("Nạp dữ liệu")
            if submitted and t_title:
                # Tạo DataFrame từ input
                data = {'title': [t_title], 'revenue': [t_rev], 'vote_average': [t_vote]}
                df_form = pd.DataFrame(data)
                clean_and_save(df_form, "Web Form")

    # --- MODE 3: GOOGLE SHEET IMPORT ---
    elif input_method == "3. Google Sheet API":
        st.info("💡 Cách dùng: Google Sheet -> File -> Share -> Publish to Web -> CSV -> Copy Link.")
        sheet_url = st.text_input("Dán Link Google Sheet (CSV):")
        
        if sheet_url and st.button("Kéo dữ liệu về"):
            try:
                df_sheet = pd.read_csv(sheet_url)
                st.write(f"Đã tìm thấy {len(df_sheet)} dòng.")
                clean_and_save(df_sheet, "Google Sheet API")
            except Exception as e:
                st.error("Lỗi: Không đọc được Link. Hãy chắc chắn link đúng định dạng CSV.")

    # --- MODE 4: OCR GENAI (VISION) ---
    elif input_method == "4. OCR Tài liệu (Ảnh/PDF)":
        st.info("🤖 Dùng Gemini Vision để đọc dữ liệu từ ảnh bảng báo cáo.")
        img_file = st.file_uploader("Upload ảnh bảng số liệu", type=["png", "jpg", "jpeg"])
        
        if img_file and "GEMINI_API_KEY" in st.secrets:
            image = Image.open(img_file)
            st.image(image, caption="Ảnh đầu vào", use_column_width=True)
            
            if st.button("Trích xuất & Lưu"):
                with st.spinner("AI đang đọc ảnh..."):
                    try:
                        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                        # Dùng model Vision chuyên đọc ảnh
                        model_vision = genai.GenerativeModel('gemini-1.5-flash') 
                        
                        prompt = """
                        Hãy đóng vai trò là OCR Engine. Trích xuất dữ liệu bảng trong ảnh này thành JSON.
                        Các trường cần lấy: title, revenue, vote_average.
                        Chỉ trả về JSON thuần list of objects. Ví dụ: [{"title": "A", "revenue": 100, "vote_average": 5}]
                        """
                        response = model_vision.generate_content([prompt, image])
                        
                        # Xử lý JSON
                        json_str = response.text.strip().replace('```json', '').replace('```', '')
                        df_ocr = pd.read_json(io.StringIO(json_str))
                        
                        st.write("Kết quả AI đọc được:")
                        st.dataframe(df_ocr)
                        clean_and_save(df_ocr, "OCR AI Vision")
                        
                    except Exception as e:
                        st.error(f"Lỗi AI OCR: {e}. Hãy thử ảnh rõ nét hơn.")

# 3. LOAD DỮ LIỆU CHO DASHBOARD
@st.cache_data
def load_data():
    engine = get_connection()
    try:
        # Lấy 10,000 dòng để phân tích
        query = f"SELECT * FROM ratings LIMIT 1000000"
        df = pd.read_sql(query, engine)
        # Chuẩn hóa tên cột ngay khi load ra
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        return df
    except Exception as e:
        return None

df = load_data()
if df is None:
    st.error(f"Lỗi: Không tìm thấy bảng 'ratings'. Hãy kiểm tra tên bảng trên Neon!")
    st.stop()

# --- XÁC ĐỊNH TÊN CỘT CHUẨN ---
title_col = 'title' if 'title' in df.columns else ('original_title' if 'original_title' in df.columns else None)
rating_col = 'vote_average' if 'vote_average' in df.columns else ('rating' if 'rating' in df.columns else None)
rev_col = 'revenue' if 'revenue' in df.columns else None

# 4. GIAO DIỆN CHÍNH
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Streamlit", "🤖 Chatbot AI", "📈 Tableau Public"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.header("Tổng quan dữ liệu")

    # KPI TỔNG QUAN
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Tổng số phim", f"{len(df):,}")

    if rating_col:
        avg_score = df[rating_col].mean()
        col_kpi2.metric("Điểm đánh giá TB", f"{avg_score:.2f} / 10")

    if rev_col:
        total_rev = df[rev_col].sum()
        col_kpi3.metric("Tổng Doanh Thu", f"${total_rev:,.0f}")

    st.divider()

    # BIỂU ĐỒ HÀNG TRÊN
    col_row2_1, col_row2_2 = st.columns(2)

    with col_row2_1:
        st.subheader("1. Phổ điểm phim (Phân bố)")
        if rating_col:
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
            top_rating_df = df.nlargest(10, rating_col).sort_values(by=rating_col, ascending=True)
            fig_rate = px.bar(top_rating_df, y=title_col, x=rating_col, orientation='h',
                              labels={title_col: "Tên phim", rating_col: "Điểm"},
                              color=rating_col, color_continuous_scale='Viridis')
            st.plotly_chart(fig_rate, use_container_width=True)
        else:
            st.warning("Thiếu cột tên phim hoặc điểm")

    # BIỂU ĐỒ DOANH THU
    st.subheader("3. Top 10 Phim Doanh Thu Cao Nhất")
    if rev_col and title_col:
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

# --- TAB 2: CHATBOT AI ---
with tab2:
    st.header("Chatbot AI phân tích phim")
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Dùng model xịn cho chat
        model = genai.GenerativeModel('models/gemini-2.0-flash') 

        if "messages" not in st.session_state: st.session_state.messages = []
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Hỏi về phim..."):
            st.chat_message("user").write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                # Kỹ thuật RAG đơn giản
                top_data = df.nlargest(5, rating_col if rating_col else df.columns[0]).to_string()
                full_prompt = f"Dữ liệu Top 5 phim:\n{top_data}\n\nCâu hỏi: {prompt}"

                resp = model.generate_content(full_prompt)
                st.chat_message("assistant").write(resp.text)
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
            except Exception as e:
                st.error(f"Lỗi AI: {e}")

# --- TAB 3: TABLEAU PUBLIC ---
with tab3:
    st.header("Báo cáo nâng cao từ Tableau")
    st.write("Dưới đây là báo cáo được tích hợp từ Tableau Public:")

    # Link Tableau của bạn (Đã sửa ký tự nối tham số)
    tableau_url = "https://public.tableau.com/views/Capstone2_102/D1?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link&:showVizHome=no&:embed=true"

    st.markdown(f"""
        <iframe src="{tableau_url}" width="100%" height="800" frameborder="0"></iframe>
    """, unsafe_allow_html=True)
