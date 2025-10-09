# =======================================================
# 🏦 ỨNG DỤNG: AI TƯ VẤN TÀI CHÍNH GIA ĐÌNH AGRIBANK SMARTFIN
# Phiên bản Demo - Dành cho kỳ thi "Cán bộ Agribank làm chủ công nghệ số"
# Tác giả: [Tên của bạn]
# =======================================================

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Agribank SmartFin - AI Tư vấn tài chính gia đình", layout="centered")

# -----------------------
# 1️⃣ GIAO DIỆN KHÁCH HÀNG
# -----------------------
st.title("🤖 Agribank SmartFin – Trợ lý tài chính gia đình thông minh")
st.write("Ứng dụng giúp khách hàng **quản lý thu chi**, **tối ưu tiết kiệm**, và **chọn gói vay phù hợp** bằng AI.")

st.header("📋 Nhập thông tin tài chính gia đình:")

income = st.number_input("💰 Thu nhập hàng tháng (VNĐ):", min_value=0, step=1000000)
expenses = st.number_input("🧾 Chi tiêu hàng tháng (VNĐ):", min_value=0, step=500000)
debt = st.number_input("💳 Tổng nợ phải trả (VNĐ):", min_value=0, step=1000000)
goal = st.selectbox("🎯 Mục tiêu tài chính:", ["Tích lũy", "Đầu tư", "Mua nhà", "Trả nợ", "Học tập", "Nghỉ hưu"])

# -----------------------
# 2️⃣ XỬ LÝ LOGIC GỢI Ý
# -----------------------
if st.button("🔍 Phân tích & Gợi ý bằng AI"):
    st.subheader("📊 Kết quả phân tích tài chính cá nhân")

    # Tính toán cơ bản
    savings_rate = round(((income - expenses) / income) * 100, 2) if income > 0 else 0
    debt_ratio = round((debt / income) * 100, 2) if income > 0 else 0

    # Gợi ý tỉ lệ khuyến nghị
    if savings_rate < 10:
        suggestion = "💡 Mức tiết kiệm còn thấp. Hãy xem xét cắt giảm chi tiêu hoặc tăng thu nhập phụ."
    elif savings_rate < 25:
        suggestion = "✅ Mức tiết kiệm khá ổn. Nên bắt đầu gửi tiết kiệm có kỳ hạn hoặc đầu tư an toàn."
    else:
        suggestion = "🏆 Tuyệt vời! Bạn có thể xem xét các gói đầu tư dài hạn hoặc trái phiếu Agribank."

    # Gợi ý sản phẩm Agribank
    if goal == "Tích lũy":
        product = "🎁 Gợi ý: Gói tiết kiệm linh hoạt Agribank – Lãi suất ~5.5%/năm."
    elif goal == "Đầu tư":
        product = "📈 Gợi ý: Gói đầu tư Agribank – Cổ phiếu ngân hàng & trái phiếu doanh nghiệp uy tín."
    elif goal == "Mua nhà":
        product = "🏠 Gợi ý: Vay mua nhà Agribank – Lãi suất ưu đãi chỉ từ 6.5%/năm."
    elif goal == "Trả nợ":
        product = "🧾 Gợi ý: Gói tái cấu trúc nợ – Gia hạn 6–12 tháng, lãi suất hỗ trợ thấp hơn 1.2%."
    else:
        product = "🌱 Gợi ý: Gói tiết kiệm hưu trí thông minh – tích lũy an toàn, lãi suất hấp dẫn."

    st.write(f"**Tỷ lệ tiết kiệm hiện tại:** {savings_rate}%")
    st.write(f"**Tỷ lệ nợ trên thu nhập:** {debt_ratio}%")
    st.success(suggestion)
    st.info(product)

    # So sánh lãi suất Big4 (giả lập)
    st.subheader("📊 So sánh lãi suất tiết kiệm (Big4)")
    data = {
        "Ngân hàng": ["Agribank", "Vietcombank", "BIDV", "Vietinbank"],
        "Lãi suất tiết kiệm (%)": [5.5, 5.3, 5.2, 5.4],
        "Lãi suất vay mua nhà (%)": [6.5, 6.8, 6.9, 6.7]
    }
    df = pd.DataFrame(data)
    st.table(df)

# -----------------------
# 3️⃣ GIAO DIỆN NHÂN VIÊN AGRIBANK
# -----------------------
st.sidebar.header("👨‍💼 Dành cho nhân viên Agribank")
st.sidebar.write("Nhập nhanh thông tin gói vay/lãi suất mới để cập nhật hệ thống:")

with st.sidebar.form("update_form"):
    product_name = st.text_input("Tên sản phẩm/gói vay:")
    rate = st.number_input("Lãi suất (%):", min_value=0.0, step=0.1)
    note = st.text_area("Ghi chú hoặc điều kiện áp dụng:")
    submitted = st.form_submit_button("📤 Cập nhật gói vay")

if submitted:
    st.sidebar.success(f"✅ Gói '{product_name}' đã được cập nhật với lãi suất {rate}%.")

st.sidebar.markdown("---")
st.sidebar.caption("Agribank SmartFin – Trợ lý tài chính số vì khách hàng Việt 🌾")
