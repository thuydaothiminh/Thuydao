# python.py - Phiên bản Hoàn chỉnh và Sửa lỗi

import streamlit as st
import pandas as pd
import numpy as np
# Cần import numpy_financial vì các hàm npv/irr đã bị loại khỏi numpy
import numpy_financial as npf 
from google import genai
from google.genai.errors import APIError
from docx import Document
import io
import re

# --- Cấu hình Trang Streamlit ---
st.set_page_config(
    page_title="App Đánh Giá Phương Án Kinh Doanh",
    layout="wide"
)

st.title("Ứng dụng Đánh giá Phương án Kinh doanh 📈")

# --- Hàm đọc file Word ---
def read_docx_file(uploaded_file):
    """Đọc nội dung văn bản từ file Word."""
    try:
        doc = Document(io.BytesIO(uploaded_file.read()))
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        return f"Lỗi đọc file Word: {e}"

# --- Hàm gọi API Gemini để trích xuất thông tin (Yêu cầu 1) ---
@st.cache_data
def extract_financial_data(doc_text, api_key):
    """Sử dụng Gemini để trích xuất các thông số tài chính từ văn bản."""
    
    if not api_key:
        raise ValueError("Khóa API không được cung cấp.")
        
    client = genai.Client(api_key=api_key)
    model_name = 'gemini-2.5-flash'
    
    # Prompt yêu cầu JSON nguyên mẫu để dễ dàng parse
    prompt = f"""
    Bạn là một chuyên gia tài chính và phân tích dự án. Nhiệm vụ của bạn là trích xuất các thông số sau từ nội dung văn bản kinh doanh bên dưới. 
    Các thông số này phải là GIÁ TRỊ SỐ, không có đơn vị (ví dụ: 1000000). 
    
    Vốn đầu tư (Initial Investment - C0): Giá trị tuyệt đối của vốn ban đầu cần bỏ ra.
    Dòng đời dự án (Project Life - N): Số năm hoạt động của dự án.
    WACC (Cost of Capital - k): Tỷ lệ chiết khấu (dạng thập phân, ví dụ: 0.10 cho 10%).
    Thuế suất (Tax Rate - t): Tỷ lệ thuế thu nhập doanh nghiệp (dạng thập phân, ví dụ: 0.20 cho 20%).
    
    Doanh thu hàng năm (Annual Revenue - R): Nếu không có thông tin chi tiết từng năm, hãy ước tính một con số đại diện cho doanh thu hàng năm.
    Chi phí hoạt động hàng năm (Annual Operating Cost - C): Nếu không có thông tin chi tiết từng năm, hãy ước tính một con số đại diện cho chi phí hoạt động hàng năm (chưa bao gồm Khấu hao).
    
    Nếu không tìm thấy thông tin cụ thể, hãy trả về 0 cho giá trị số (trừ WACC và Thuế suất nên là 0.2 nếu không tìm thấy).

    Định dạng đầu ra **bắt buộc** là JSON nguyên mẫu (RAW JSON), không có bất kỳ giải thích hay văn bản nào khác.
    
    {{
      "Vốn đầu tư": <Giá trị số>,
      "Dòng đời dự án": <Giá trị số năm>,
      "Doanh thu hàng năm": <Giá trị số>,
      "Chi phí hoạt động hàng năm": <Giá trị số>,
      "WACC": <Giá trị số thập phân>,
"Thuế suất": <Giá trị số thập phân>
    }}

    Nội dung file Word:
    ---
    {doc_text}
    """

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    
    # Xử lý chuỗi JSON trả về
    json_str = response.text.strip().replace("```json", "").replace("```", "").strip()
    return pd.read_json(io.StringIO(json_str), typ='series')

# --- Hàm tính toán Chỉ số Tài chính (Yêu cầu 3) ---
def calculate_project_metrics(df_cashflow, initial_investment, wacc):
    """Tính toán NPV, IRR, PP, DPP."""
    
    cash_flows = df_cashflow['Dòng tiền thuần (CF)'].values
    
    # 1. NPV
    # Thêm vốn đầu tư ban đầu vào đầu dòng tiền
    full_cash_flows = np.insert(cash_flows, 0, -initial_investment) 
    
    # Dùng npf.npv
    npv_value = npf.npv(wacc, full_cash_flows)
    
    # 2. IRR
    try:
        # Dùng npf.irr
        irr_value = npf.irr(full_cash_flows)
    except ValueError:
        irr_value = np.nan 

    # 3. PP (Payback Period - Thời gian hoàn vốn)
    cumulative_cf = np.cumsum(full_cash_flows)
    pp_year = np.where(cumulative_cf >= 0)[0]
    if pp_year.size > 0:
        pp_year = pp_year[0]
        if pp_year == 0: 
             pp = 0 
        else:
             capital_remaining = abs(cumulative_cf[pp_year-1])
             cf_of_payback_year = cash_flows[pp_year-1]
             pp = pp_year - 1 + (capital_remaining / cf_of_payback_year) if cf_of_payback_year != 0 else pp_year 
    else:
        pp = 'Không hoàn vốn'

    # 4. DPP (Discounted Payback Period - Thời gian hoàn vốn có chiết khấu)
    discount_factors = 1 / ((1 + wacc) ** np.arange(0, len(full_cash_flows)))
    discounted_cf = full_cash_flows * discount_factors
    cumulative_dcf = np.cumsum(discounted_cf)
    
    dpp_year = np.where(cumulative_dcf >= 0)[0]
    if dpp_year.size > 0:
        dpp_year = dpp_year[0]
        if dpp_year == 0:
             dpp = 0
        else:
             capital_remaining_d = abs(cumulative_dcf[dpp_year-1])
             dcf_of_payback_year = discounted_cf[dpp_year] 
             dpp = dpp_year - 1 + (capital_remaining_d / dcf_of_payback_year) if dcf_of_payback_year != 0 else dpp_year
    else:
        dpp = 'Không hoàn vốn'
        
    return npv_value, irr_value, pp, dpp

# --- Hàm gọi AI phân tích chỉ số (Yêu cầu 4) ---
def get_ai_evaluation(metrics_data, wacc_rate, api_key):
    """Gửi các chỉ số đánh giá dự án đến Gemini API và nhận phân tích."""
    
    if not api_key:
        return "Lỗi: Khóa API không được cung cấp."

    try:
        client = genai.Client(api_key=api_key)
        model_name = 'gemini-2.5-flash'  

        prompt = f"""
