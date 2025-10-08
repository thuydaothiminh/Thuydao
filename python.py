# python.py - Phiên bản Hoàn chỉnh và Sửa lỗi

import streamlit as st
import pandas as pd
import numpy as np
# Cần import numpy_financial vì các hàm npv/irr đã bị loại khỏi numpy
# import numpy_financial as npf 
from google import genai
from google.genai.errors import APIError
from docx import Document
import io
import re

# Cấu hình API key cho Google Gemini
# Nên sử dụng st.secrets để lưu key an toàn
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Lỗi: Không tìm thấy khóa API 'GEMINI_API_KEY' trong Streamlit Secrets. Vui lòng thêm khóa của bạn.")
    st.stop()
except Exception as e:
    st.error(f"Đã xảy ra lỗi khi cấu hình API: {e}")
    st.stop()

# --- Cấu hình Trang Streamlit ---
st.set_page_config(
    page_title="Phân Tích Phương Án Kinh Doanh 🚀",
    layout="wide"
)

st.title("Ứng dụng Phân Tích Phương Án Kinh Doanh (PVT-Pro) 📊")
st.markdown("Sử dụng AI để tự động trích xuất dữ liệu, tính toán và phân tích hiệu quả dự án từ file Word.")

# --- Các hàm xử lý cốt lõi ---

# 1. Hàm trích xuất thông tin bằng AI từ file Word
def extract_project_info_ai(doc_content):
    """Sử dụng Gemini AI để trích xuất các thông tin tài chính từ nội dung văn bản."""
    prompt = f"""
    Bạn là một chuyên gia phân tích tài chính. Hãy đọc và trích xuất các thông tin sau từ nội dung văn bản dưới đây. Nếu không tìm thấy thông tin nào, hãy để giá trị là 'N/A'.
    Hãy trả về kết quả dưới dạng một chuỗi JSON.
    Nội dung văn bản:
    ---
    {doc_content}
    ---
    Cấu trúc JSON cần trích xuất:
    {{
        "Vốn đầu tư": "Giá trị số",
        "Dòng đời dự án": "Giá trị số (năm)",
        "Doanh thu": "Giá trị số (có thể là dòng tiền hàng năm hoặc tổng)",
        "Chi phí": "Giá trị số (có thể là dòng tiền hàng năm hoặc tổng)",
        "WACC": "Giá trị số (%)",
        "Thuế": "Giá trị số (%)"
    }}
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt, stream=True)
    response.resolve()
    
    # Trích xuất chuỗi JSON từ phản hồi
    json_string = response.text.strip().replace('```json', '').replace('```', '')
    
    # Xử lý các lỗi phổ biến trong chuỗi JSON
    try:
        # Cố gắng tải JSON
        import json
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        # Xử lý khi JSON không hợp lệ, cố gắng trích xuất thủ công
        st.warning("AI phản hồi không phải là JSON hợp lệ. Đang cố gắng trích xuất thủ công.")
        
        extracted_data = {}
        # Sử dụng biểu thức chính quy để tìm các giá trị
        patterns = {
            "Vốn đầu tư": r'"Vốn đầu tư":\s*"(.*?)"',
            "Dòng đời dự án": r'"Dòng đời dự án":\s*"(.*?)"',
            "Doanh thu": r'"Doanh thu":\s*"(.*?)"',
            "Chi phí": r'"Chi phí":\s*"(.*?)"',
            "WACC": r'"WACC":\s*"(.*?)"',
            "Thuế": r'"Thuế":\s*"(.*?)"'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, json_string)
            if match:
                extracted_data[key] = match.group(1)
            else:
                extracted_data[key] = "N/A"
        return extracted_data

# 2. Hàm tính toán các chỉ số tài chính
def calculate_financial_metrics(cf, wacc):
    """Tính toán NPV, IRR, PP và DPP."""
    # cf: cash flow (dòng tiền)
    # wacc: weighted average cost of capital
    
    cf_df = pd.DataFrame(cf, columns=['Năm', 'Dòng tiền'])
    
    # Tính NPV (Net Present Value)
    npv = sum(cf_df['Dòng tiền'].iloc[i] / (1 + wacc)**i for i in range(1, len(cf_df))) - abs(cf_df['Dòng tiền'].iloc[0])

    # Tính IRR (Internal Rate of Return)
    try:
        from scipy.optimize import newton
        def irr_equation(irr):
            return sum(cf_df['Dòng tiền'].iloc[i] / (1 + irr)**i for i in range(1, len(cf_df))) - abs(cf_df['Dòng tiền'].iloc[0])
        irr = newton(irr_equation, x0=wacc)
    except (RuntimeError, ValueError):
        irr = float('nan') # Không tính được IRR

    # Tính PP (Payback Period)
    cumulative_cf = [cf_df['Dòng tiền'].iloc[0]]
    for i in range(1, len(cf_df)):
        cumulative_cf.append(cumulative_cf[i-1] + cf_df['Dòng tiền'].iloc[i])
    
    pp = "N/A"
    for i in range(1, len(cumulative_cf)):
        if cumulative_cf[i] >= 0:
            if cumulative_cf[i-1] < 0:
                pp = (i-1) + abs(cumulative_cf[i-1]) / cf_df['Dòng tiền'].iloc[i]
            else:
                pp = i-1
            break
            
    # Tính DPP (Discounted Payback Period)
    discounted_cf = [cf_df['Dòng tiền'].iloc[i] / (1 + wacc)**i for i in range(1, len(cf_df))]
    discounted_cf.insert(0, cf_df['Dòng tiền'].iloc[0])
    
    cumulative_dcf = [discounted_cf[0]]
    for i in range(1, len(discounted_cf)):
        cumulative_dcf.append(cumulative_dcf[i-1] + discounted_cf[i])
        
    dpp = "N/A"
    for i in range(1, len(cumulative_dcf)):
        if cumulative_dcf[i] >= 0:
            if cumulative_dcf[i-1] < 0:
                dpp = (i-1) + abs(cumulative_dcf[i-1]) / discounted_cf[i]
            else:
                dpp = i-1
            break

    return npv, irr, pp, dpp

# 3. Hàm phân tích chỉ số bằng AI
def analyze_metrics_ai(npv, irr, pp, dpp, wacc):
    """Sử dụng Gemini AI để phân tích các chỉ số tài chính."""
    prompt = f"""
    Bạn là một chuyên gia phân tích dự án đầu tư. Dựa trên các chỉ số hiệu quả dự án sau, hãy đưa ra một nhận xét chuyên nghiệp và khách quan. Nhận xét cần ngắn gọn, tập trung vào việc liệu dự án có khả thi hay không.

    Các chỉ số cần phân tích:
    - NPV (Giá trị hiện tại ròng): {npv:,.2f}
    - IRR (Tỷ suất sinh lời nội tại): {irr:.2%}
    - WACC (Chi phí vốn bình quân): {wacc:.2%}
    - PP (Thời gian hoàn vốn): {pp:.2f} năm
    - DPP (Thời gian hoàn vốn có chiết khấu): {dpp:.2f} năm

    Đánh giá dựa trên các tiêu chí sau:
    1. NPV > 0: Dự án khả thi.
    2. IRR > WACC: Dự án có lợi nhuận cao hơn chi phí vốn.
    3. PP và DPP: Dự án hoàn vốn nhanh hay chậm?
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt, stream=True)
    response.resolve()
    return response.text

# --- Giao diện và Luồng Ứng dụng ---
uploaded_file = st.file_uploader(
    "1. Tải lên file Word (.docx) chứa phương án kinh doanh",
    type=['docx']
)

# Khởi tạo trạng thái phiên
if 'project_info' not in st.session_state:
    st.session_state.project_info = None
if 'cash_flow_data' not in st.session_state:
    st.session_state.cash_flow_data = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
    
# Chức năng 1: Lọc thông tin dự án bằng AI
if uploaded_file:
    st.success("File đã được tải lên thành công!")
    
    if st.button("Trích xuất thông tin bằng AI", key="extract_button"):
        with st.spinner('Đang đọc và phân tích file...'):
            try:
                doc = Document(uploaded_file)
                full_text = " ".join([paragraph.text for paragraph in doc.paragraphs])
                
                # Trích xuất thông tin
                st.session_state.project_info = extract_project_info_ai(full_text)
                st.success("Trích xuất dữ liệu hoàn tất!")

            except Exception as e:
                st.error(f"Có lỗi xảy ra khi xử lý file: {e}")

if st.session_state.project_info:
    st.subheader("2. Thông tin dự án đã trích xuất")
    # Hiển thị các thông tin đã trích xuất
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Vốn đầu tư", st.session_state.project_info.get("Vốn đầu tư", "N/A"))
        st.metric("Dòng đời dự án", st.session_state.project_info.get("Dòng đời dự án", "N/A"))
        st.metric("WACC", st.session_state.project_info.get("WACC", "N/A"))
    with col2:
        st.metric("Doanh thu", st.session_state.project_info.get("Doanh thu", "N/A"))
        st.metric("Chi phí", st.session_state.project_info.get("Chi phí", "N/A"))
        st.metric("Thuế", st.session_state.project_info.get("Thuế", "N/A"))
        
    st.info("⚠️ Vui lòng kiểm tra và chỉnh sửa các giá trị trên cho chính xác trước khi tính toán.")
    
    # Thêm form cho người dùng chỉnh sửa và nhập liệu thủ công
    with st.expander("Chỉnh sửa dữ liệu (nếu cần)"):
        st.session_state.project_info["Vốn đầu tư"] = st.number_input("Vốn đầu tư", value=float(st.session_state.project_info.get("Vốn đầu tư", 0).replace(',', '').replace(' VND', '')), format="%.0f")
        st.session_state.project_info["Dòng đời dự án"] = st.number_input("Dòng đời dự án (năm)", value=int(st.session_state.project_info.get("Dòng đời dự án", 1)), format="%d")
        st.session_state.project_info["Doanh thu"] = st.number_input("Doanh thu hàng năm", value=float(st.session_state.project_info.get("Doanh thu", 0).replace(',', '').replace(' VND', '')), format="%.0f")
        st.session_state.project_info["Chi phí"] = st.number_input("Chi phí hàng năm", value=float(st.session_state.project_info.get("Chi phí", 0).replace(',', '').replace(' VND', '')), format="%.0f")
        st.session_state.project_info["WACC"] = st.number_input("WACC (%)", value=float(st.session_state.project_info.get("WACC", 0).replace('%', '')), min_value=0.0, max_value=100.0)
        st.session_state.project_info["Thuế"] = st.number_input("Thuế (%)", value=float(st.session_state.project_info.get("Thuế", 0).replace('%', '')), min_value=0.0, max_value=100.0)
    
    # Chức năng 2: Xây dựng bảng dòng tiền
    if st.button("Xây dựng Bảng dòng tiền"):
        try:
            initial_investment = -abs(st.session_state.project_info["Vốn đầu tư"])
            project_life = int(st.session_state.project_info["Dòng đời dự án"])
            revenue = st.session_state.project_info["Doanh thu"]
            cost = st.session_state.project_info["Chi phí"]
            tax_rate = st.session_state.project_info["Thuế"] / 100
            
            # Tính toán dòng tiền hàng năm (ví dụ đơn giản)
            cash_flow_annually = (revenue - cost) * (1 - tax_rate)
            
            cash_flow_table = {
                'Năm': [0] + list(range(1, project_life + 1)),
                'Dòng tiền': [initial_investment] + [cash_flow_annually] * project_life
            }
            st.session_state.cash_flow_data = cash_flow_table
            
        except Exception as e:
            st.error(f"Lỗi khi tạo bảng dòng tiền: {e}. Vui lòng kiểm tra lại các giá trị đầu vào.")

if st.session_state.cash_flow_data:
    st.subheader("3. Bảng Dòng tiền Dự án")
    df_cf = pd.DataFrame(st.session_state.cash_flow_data)
    st.dataframe(df_cf.style.format({'Dòng tiền': '{:,.0f}'}), use_container_width=True)

    # Chức năng 3: Tính toán các chỉ số
    if st.button("Tính toán các Chỉ số Hiệu quả"):
        try:
            wacc = st.session_state.project_info["WACC"] / 100
            npv, irr, pp, dpp = calculate_financial_metrics(st.session_state.cash_flow_data, wacc)
            st.session_state.metrics = {
                "NPV": npv,
                "IRR": irr,
                "PP": pp,
                "DPP": dpp,
                "WACC": wacc
            }
            st.success("Đã tính toán xong các chỉ số!")
        except Exception as e:
            st.error(f"Lỗi khi tính toán chỉ số: {e}. Vui lòng kiểm tra lại các giá trị đầu vào.")

if st.session_state.metrics:
    st.subheader("4. Các Chỉ số Đánh giá Hiệu quả")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("NPV", f"{st.session_state.metrics['NPV']:,.2f}")
    col2.metric("IRR", f"{st.session_state.metrics['IRR']:.2%}" if not pd.isna(st.session_state.metrics['IRR']) else "N/A")
    col3.metric("PP (năm)", f"{st.session_state.metrics['PP']:.2f}")
    col4.metric("DPP (năm)", f"{st.session_state.metrics['DPP']:.2f}")

    # Chức năng 4: Phân tích chỉ số bằng AI
    if st.button("Yêu cầu AI Phân tích"):
        with st.spinner('Đang gửi dữ liệu và chờ Gemini phân tích...'):
            try:
                ai_analysis = analyze_metrics_ai(
                    st.session_state.metrics['NPV'],
                    st.session_state.metrics['IRR'],
                    st.session_state.metrics['PP'],
                    st.session_state.metrics['DPP'],
                    st.session_state.metrics['WACC']
                )
                st.markdown("---")
                st.subheader("5. Kết quả Phân tích từ Gemini AI")
                st.info(ai_analysis)
            except Exception as e:
                st.error(f"Lỗi khi yêu cầu phân tích AI: {e}")

st.markdown("---")
st.markdown("Phát triển bởi 🤖 Chuyên gia lập trình Streamlit.")
