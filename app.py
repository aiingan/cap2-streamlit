import streamlit as st
import google.generativeai as genai

st.title("🤖 Kiểm tra kết nối AI Gemini")

# 1. Lấy API Key từ Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Chưa tìm thấy GEMINI_API_KEY trong Secrets!")
    st.stop()

# 2. Cấu hình
genai.configure(api_key=api_key)

st.write("Đang kết nối với Google để lấy danh sách Model...")

# 3. Liệt kê tất cả Model khả dụng
try:
    st.subheader("Danh sách Model bạn được phép dùng:")
    
    available_models = []
    for m in genai.list_models():
        # Chỉ lấy các model hỗ trợ tạo văn bản (generateContent)
        if 'generateContent' in m.supported_generation_methods:
            st.write(f"- `{m.name}`")
            available_models.append(m.name)
            
    if not available_models:
        st.warning("⚠️ Không tìm thấy model nào! Có thể API Key bị lỗi hoặc giới hạn vùng.")
    else:
        st.success(f"✅ Tìm thấy {len(available_models)} model.")
        
except Exception as e:
    st.error(f"❌ Lỗi khi gọi Google: {e}")
    st.info("Gợi ý: Kiểm tra lại API Key xem có copy thừa dấu cách không?")
