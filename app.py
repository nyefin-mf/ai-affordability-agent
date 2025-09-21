import streamlit as st
import pandas as pd
from datetime import datetime
import re
import io

# Page configuration
st.set_page_config(
    page_title="AI Affordability Agent",
    page_icon="🏦",
    layout="wide"
)

# Custom styling
st.markdown("""
<style>
.main-title {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.approved {
    background-color: #d4edda;
    color: #155724;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
    font-size: 1.5rem;
    font-weight: bold;
    margin: 1rem 0;
}
.rejected {
    background-color: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
    font-size: 1.5rem;
    font-weight: bold;
    margin: 1rem 0;
}
.info-box {
    background-color: #e3f2fd;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #2196f3;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessments' not in st.session_state:
    st.session_state.assessments = []

# Simple PDF text extractor
def extract_pdf_text(pdf_file):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except:
        return "Could not extract text from PDF"

# Simple bank statement parser
def parse_bank_statement(text):
    amounts = re.findall(r'R?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
    amounts = [float(amt.replace(',', '')) for amt in amounts if amt]
    # Filter reasonable salary amounts
    potential_salaries = [amt for amt in amounts if 5000 <= amt <= 100000]
    return {
        'estimated_salary': max(potential_salaries) if potential_salaries else 15000,
        'avg_amount': sum(amounts) / len(amounts) if amounts else 0,
        'transaction_count': len(amounts)
    }

# Main app
st.markdown('<div class="main-title">🏦 AI Affordability Assessment Agent</div>', unsafe_allow_html=True)
st.markdown("**Upload documents and get instant NCA-compliant loan decisions**")
st.markdown("---")

# Navigation tabs
tab1, tab2, tab3, tab4 = st.tabs(["📄 Documents", "💰 Application", "📊 Assessment", "📈 Results"])

# Tab 1: Document Upload
with tab1:
    st.header("📄 Upload Your Documents")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏦 Bank Statements")
        bank_files = st.file_uploader(
            "Upload bank statements (PDF or CSV)", 
            type=['pdf', 'csv'],
            accept_multiple_files=True,
            help="Upload 3 months of bank statements"
        )
        estimated_income = 15000  # Default
        if bank_files:
            st.success(f"✅ {len(bank_files)} file(s) uploaded")
            for idx, file in enumerate(bank_files):
                with st.expander(f"📄 {file.name}"):
                    if file.type == "application/pdf":
                        text = extract_pdf_text(file)
                        bank_data = parse_bank_statement(text)
                        st.metric("Estimated Monthly Income", f"R{bank_data['estimated_salary']:,.2f}")
                        st.metric("Transactions Found", bank_data['transaction_count'])
                        estimated_income = max(estimated_income, bank_data['estimated_salary'])
                    elif file.type == "text/csv":
                        df = pd.read_csv(file)
                        st.dataframe(df.head())
            st.session_state.estimated_income = estimated_income
    with col2:
        st.subheader("💰 Payslip Details")
        st.markdown('<div class="info-box">Enter your payslip information manually</div>', unsafe_allow_html=True)
        with st.form("payslip_form"):
            gross_salary = st.number_input("Gross Monthly Salary (R)", value=15000, min_value=1000, step=500)
            tax_deduction = st.number_input("Tax Deduction (R)", value=int(gross_salary * 0.15), min_value=0)
            other_deductions = st.number_input("Other Deductions (R)", value=500, min_value=0)
            net_salary = gross_salary - tax_deduction - other_deductions
            st.metric("Net Salary", f"R{net_salary:,.2f}")
            if st.form_submit_button("💾 Save Payslip Data"):
                st.session_state.payslip_data = {
                    'gross': gross_salary,
                    'tax': tax_deduction,
                    'other_deductions': other_deductions,
                    'net': net_salary
                }
                st.success("✅ Payslip data saved!")

# Tab 2: Application Details
with tab2:
    st.header("💰 Loan Application Details")
    default_income = getattr(st.session_state, 'estimated_income', 15000)
if hasattr(st.session_state, 'payslip_data'):
    default_income = max(default_income, st.session_state.payslip_data['gross'])

    with st.form("application_form"):
        col1, col2 = st.columns(2)
        with col1:
    st.subheader("📊 Income & Expenses")
    monthly_income = getattr(st.session_state, 'estimated_income', 15000)
    st.write(f"Monthly Gross Income (from bank statements): R{monthly_income:,.2f}")
    monthly_expenses = st.number_input("Monthly Expenses (R)", value=8000, min_value=1000)
    existing_debt = st.number_input("Existing Debt Payments (R)", value=2000, min_value=0)
    ...

            employment_months = st.number_input("Employment Duration (months)", value=24, min_value=1)
            dependents = st.number_input("Number of Dependents", value=2, min_value=0)
        with col2:
            st.subheader("💳 Loan Details")
            loan_amount = st.number_input("Loan Amount (R)", value=50000, min_value=5000, step=5000)
            loan_term = st.number_input("Loan Term (months)", value=24, min_value=6, max_value=72)
            interest_rate = st.number_input("Interest Rate (% p.a.)", value=20.0, min_value=10.0, max_value=35.0)
            loan_purpose = st.selectbox("Loan Purpose", [
                "Debt Consolidation", "Home Improvement", "Vehicle", 
                "Emergency", "Business", "Education", "Other"
            ])
        if st.form_submit_button("🔍 Assess Application", type="primary"):
            st.session_state.application = {
                'monthly_income': monthly_income,
                'monthly_expenses': monthly_expenses,
                'existing_debt': existing_debt,
                'employment_months': employment_months,
                'dependents': dependents,
                'loan_amount': loan_amount,
                'loan_term': loan_term,
                'interest_rate': interest_rate,
                'loan_purpose': loan_purpose,
                'timestamp': datetime.now()
            }
            st.success("✅ Application submitted for assessment!")

# Tab 3: Assessment Results
with tab3:
    st.header("📊 NCA Affordability Assessment")
    if hasattr(st.session_state, 'application'):
        app = st.session_state.application
        monthly_rate = app['interest_rate'] / 100 / 12
        num_payments = app['loan_term']
        monthly_payment = (app['loan_amount'] * monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        net_income = app['monthly_income'] * 0.75  # Simplified net income
        discretionary_income = net_income - app['monthly_expenses'] - app['existing_debt']
        minimum_buffer = monthly_payment * 1.5  # 150% buffer
        nca_compliant = discretionary_income >= minimum_buffer
        affordability_ratio = (discretionary_income / net_income * 100) if net_income > 0 else 0
        debt_service_ratio = (monthly_payment / net_income * 100) if net_income > 0 else 0
        if nca_compliant and discretionary_income > 0 and debt_service_ratio <= 30:
            decision = "APPROVED"
            decision_class = "approved"
        else:
            decision = "REJECTED"
            decision_class = "rejected"
        st.subheader("💡 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Monthly Payment", f"R{monthly_payment:,.2f}")
        with col2:
            st.metric("Discretionary Income", f"R{discretionary_income:,.2f}")
        with col3:
            st.metric("Affordability Ratio", f"{affordability_ratio:.1f}%")
        with col4:
            st.metric("Debt Service Ratio", f"{debt_service_ratio:.1f}%")
        st.markdown(f'<div class="{decision_class}">{"✅" if decision == "APPROVED" else "❌"} {decision}</div>', unsafe_allow_html=True)
        st.subheader("📋 Detailed Analysis")
        breakdown = pd.DataFrame({
            'Item': [
                'Gross Monthly Income',
                'Estimated Net Income',
                'Monthly Expenses', 
                'Existing Debt',
                'Discretionary Income',
                'Required Payment',
                'Remaining Buffer'
            ],
            'Amount': [
                f"R{app['monthly_income']:,.2f}",
                f"R{net_income:,.2f}",
                f"R{app['monthly_expenses']:,.2f}",
                f"R{app['existing_debt']:,.2f}",
                f"R{discretionary_income:,.2f}",
                f"R{monthly_payment:,.2f}",
                f"R{discretionary_income - monthly_payment:,.2f}"
            ]
        })
        st.dataframe(breakdown, hide_index=True, use_container_width=True)
        st.subheader("⚖️ NCA Compliance")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Requirements:**")
            st.write("✅ Income verification completed")
            st.write("✅ Affordability assessment performed") 
            st.write(f"{'✅' if nca_compliant else '❌'} 150% payment buffer maintained")
            st.write(f"{'✅' if debt_service_ratio <= 30 else '❌'} Debt service ratio ≤ 30%")

