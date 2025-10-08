import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai

# ======================
# 🔧 CẤU HÌNH ỨNG DỤNG
# ======================
st.set_page_config(page_title="AGR – TƯ VẤN TÀI CHÍNH AI", layout="wide", page_icon="💰")
st.title("💬 AGR – Trợ lý Tư vấn Tài chính AI của Agribank")

st.markdown("""
Ứng dụng mô phỏng hệ thống tư vấn tài chính cá nhân của Agribank.
AI sẽ giúp bạn **đưa ra lựa chọn vay, gửi hoặc đầu tư** dựa trên dữ liệu tài chính cá nhân.
""")

# ======================
# 🧩 NHẬP THÔNG TIN KHÁCH HÀNG
# ======================
st.sidebar.header("📥 Thông tin khách hàng")
income = st.sidebar.number_input("Thu nhập bình quân tháng (triệu VND)", 0.0, 1000.0, 30.0)
expense = st.sidebar.number_input("Chi tiêu cố định/tháng (triệu VND)", 0.0, 1000.0, 15.0)
debt = st.sidebar.number_input("Tổng nợ hiện tại (triệu VND)", 0.0, 2000.0, 200.0)
saving = st.sidebar.number_input("Số tiền có thể tiết kiệm/đầu tư (triệu VND)", 0.0, 2000.0, 300.0)
purpose = st.sidebar.selectbox("Mục đích vay", ["Mua nhà", "Mua xe", "Tiêu dùng", "Học phí", "Đầu tư"])
duration = st.sidebar.slider("Thời gian vay mong muốn (năm)", 1, 30, 10)
risk_level = st.sidebar.radio("Mức độ chấp nhận rủi ro", ["Thấp", "Trung bình", "Cao"])

# ======================
# ⚙️ HÀM XỬ LÝ TÀI CHÍNH
# ======================
def analyze_finance(income, expense, debt, saving, risk_level):
    disposable = income - expense
    dsr = debt / max(income, 1e-6)
    saving_rate = saving / max(income, 1e-6)

    advice = ""
    if dsr > 0.6:
        advice = "⚠️ Nợ hiện tại cao, nên giảm nợ hoặc gửi tiết kiệm."
    elif saving_rate > 0.3 and risk_level != "Thấp":
        advice = "💹 Bạn có khả năng đầu tư để tối ưu lợi nhuận."
    else:
        advice = "💰 Bạn nên xem xét gửi tiết kiệm hoặc vay tiêu dùng nhẹ."

    return disposable, dsr, saving_rate, advice


# ======================
# 🧮 GỢI Ý TÀI CHÍNH
# ======================
disposable, dsr, saving_rate, financial_advice = analyze_finance(income, expense, debt, saving, risk_level)

st.subheader("📊 Kết quả phân tích tài chính cá nhân")
col1, col2, col3 = st.columns(3)
col1.metric("Thu nhập khả dụng", f"{disposable:.1f} triệu", "VND/tháng")
col2.metric("Tỷ lệ nợ trên thu nhập (DSR)", f"{dsr*100:.1f}%", "Cảnh báo nếu >60%")
col3.metric("Tỷ lệ tiết kiệm", f"{saving_rate*100:.1f}%", "Khả năng đầu tư/gửi")

st.info(financial_advice)

# ======================
# 🔍 BẢNG SO SÁNH NGÂN HÀNG
# ======================
st.subheader("🏦 So sánh các gói vay/gửi giữa ngân hàng")
data = {
    "Ngân hàng": ["Agribank", "Vietcombank", "BIDV", "VietinBank"],
    "Lãi suất vay (%)": [9.5, 10.2, 9.8, 9.7],
    "Lãi suất gửi (%)": [6.5, 6.2, 6.4, 6.3],
    "Kỳ hạn vay (năm)": [duration, duration, duration, duration],
    "TSBĐ yêu cầu": ["Có", "Có", "Có", "Có"],
}
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)

fig = px.bar(df, x="Ngân hàng", y=["Lãi suất vay (%)", "Lãi suất gửi (%)"],
             barmode="group", title="So sánh lãi suất vay & gửi")
st.plotly_chart(fig, use_container_width=True)

# ======================
# 💬 KHUNG CHAT VỚI GEMINI
# ======================
st.subheader("💬 Tư vấn AI – AGR Gemini Chat")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Vui lòng cấu hình khóa GEMINI_API_KEY trong Streamlit Secrets.")
else:
    user_message = st.chat_input("Nhập câu hỏi của bạn về vay, gửi, đầu tư...")

    if user_message:
        with st.chat_message("user"):
            st.markdown(user_message)

        client = genai.Client(api_key=api_key)
        model_name = "gemini-2.5-flash"

        context = f"""
        Bạn là trợ lý tài chính Agribank.
        Dữ liệu khách hàng:
        - Thu nhập: {income} triệu/tháng
        - Chi tiêu: {expense} triệu/tháng
        - Nợ: {debt} triệu
        - Tiết kiệm: {saving} triệu
        - Mục đích: {purpose}
        - Mức rủi ro: {risk_level}

        Hãy tư vấn phù hợp cho khách hàng này.
        """

        with st.chat_message("assistant"):
            with st.spinner("🤖 Gemini đang phản hồi..."):
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"{context}\nCâu hỏi: {user_message}"
                )
                message = response.text
                st.markdown(message)
                st.session_state.chat_history.append({"user": user_message, "ai": message})

# ======================
# 📈 PHÂN TÍCH LỢI ÍCH SONG SONG
# ======================
st.subheader("📈 Lợi ích song song: Khách hàng & Ngân hàng")
nim = 9.5 - 6.5
st.markdown(f"""
| Đối tượng | Lợi ích chính |
|------------|----------------|
| **Khách hàng** | Lãi gửi: 6.5%/năm  → ~{saving*0.065:.1f} triệu/năm |
| **Ngân hàng (Agribank)** | Biên lợi nhuận NIM ≈ {nim:.1f}% |
| **Cả hai bên** | Giao dịch ổn định, tăng niềm tin và thu nhập dài hạn |
""")

st.success("✅ Hệ thống 'AGR – Tư vấn Tài chính AI' sẵn sàng hỗ trợ khách hàng 24/7.")
