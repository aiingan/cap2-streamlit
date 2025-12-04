import streamlit as st
from sqlalchemy import create_engine

# Dùng @st.cache_resource để Streamlit không kết nối lại DB liên tục gây chậm
@st.cache_resource
def get_engine():
    # Chuỗi kết nối lấy từ notebook cũ của bạn
    # Lưu ý: Passwords nên để trong secrets, nhưng để chạy nhanh ta tạm để đây
    connection_string = "postgresql+psycopg2://neondb_owner:npg_deE7FBOQ3Cuc@ep-lingering-voice-a1cvl42u-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    engine = create_engine(connection_string)
    return engine
