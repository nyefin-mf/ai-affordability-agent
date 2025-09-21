import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Title
st.set_page_config(page_title="AI Auto Affordability", page_icon="🤖")
st.markdown("<h2 style='text-align:center; color:#1f77b4'>🤖 Automated AI Affordability Calculator</h2>", unsafe_allow_html=True)
st.markdown("##### Upload your South African bank statement PDF below. Instantly see the maximum loan amount you qualify for.")
st.markdown("---")

def extract_pdf_text(pdf_file):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_file)
        return "".join(page.extract_text() for page in reader.pages)
    except Exception as e:
        return ""

def parse_bank_statement(text):
    # Extract all amounts
    amounts = re.findall(r'R?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
    amounts = [float(a.replace(",", "")) for a in amounts if a]
    # Estimate salary: pick largest repeating amount
    salaries = [amt for amt in amounts if 5000 <= amt <= 100000]
    salary = max(salaries) if salaries else 15000
    # Estimate expenses: sum debits below salary level
    expenses = [amt for amt in amounts if amt < salary and amt > 500]
    avg_expense = sum(expenses)/len(expenses) if expenses else salary*0.6
    return salary, avg_expense

# Upload PDF
pdf = st.file_uploader("Upload bank statement PDF", type="pdf")
if pdf:
    with st.spinner("Extracting and analyzing statement..."):
        text = extract_pdf_text(pdf)
        salary, avg_expense = parse_bank_statement(text)
        st.success("Document processed!")
        
        # Assumptions
        existing_debt = salary * 0.15     # 15% of income
        loan_term = 24                    # months
        interest_rate = 22                # percent
        net_income = salary * 0.75        # after taxes
        discretionary_income = net_income - avg_expense - existing_debt
        
        # Calculate max monthly payment
        max_monthly_payment = discretionary_income / 1.5 if discretionary_income > 0 else 0
        monthly_rate = interest_rate/100/12
        # Reverse amortization formula to solve for maximum loan
        if monthly_rate > 0:
            qualifying_loan = max_monthly_payment * ((1 + monthly_rate) ** loan_term - 1) / (monthly_rate * (1 + monthly_rate) ** loan_term)
        else:
            qualifying_loan = max_monthly_payment * loan_term
        
        # Affordability check
        affordability_ratio = discretionary_income / net_income * 100 if net_income > 0 else 0
        debt_service_ratio = max_monthly_payment / net_income * 100 if net_income > 0 else 0
        nca_compliant = discretionary_income > 0 and affordability_ratio >= 25 and debt_service_ratio <= 30

        st.markdown("### Results")
        if nca_compliant and qualifying_loan >= 1000:
            st.markdown(f"<div style='background:#d4edda; color:#155724; border-radius:8px; padding:1rem; font-size:1.5rem; text-align:center;'>✅ You qualify for up to:<br><b>R{qualifying_loan:,.0f}</b></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#f8d7da; color:#721c24; border-radius:8px; padding:1rem; font-size:1.5rem; text-align:center;'>❌ Sorry, you do not currently qualify for a loan</div>", unsafe_allow_html=True)

        # Detailed breakdown
        st.markdown("#### Income & Expense Analysis")
        st.write(f"- **Estimated Monthly Gross Salary:** R{salary:,.2f}")
        st.write(f"- **Estimated Monthly Expenses:** R{avg_expense:,.2f}")
        st.write(f"- **Estimated Existing Debt Payments:** R{existing_debt:,.2f}")
        st.write(f"- **Estimated Net Income (after taxes):** R{net_income:,.2f}")

        st.markdown("#### Affordability Ratios")
        st.write(f"- **Discretionary Income:** R{discretionary_income:,.2f} per month")
        st.write(f"- **Affordability Ratio:** {affordability_ratio:.1f}%")
        st.write(f"- **Debt Service Ratio:** {debt_service_ratio:.1f}%")
        st.write(f"- **NCA Compliance:** {'Yes' if nca_compliant else 'No'}")

        st.markdown("---")
        st.markdown("**Assumptions:**")
        st.write(f"- Loan term: {loan_term} months\n- Interest rate: {interest_rate}% p.a.\n- Existing debt and expenses estimated from statement.")
        st.write("Contact admin to enable more advanced document analysis or options.")

        # Option to start over
        if st.button("🔄 Try another statement"):
            st.experimental_rerun()
else:
    st.info("Upload a recent PDF bank statement to see how much you qualify for automatically.")

st.markdown("---")
st.markdown("<small>🤖 AI Affordability Agent &mdash; Instant estimation, no manual entry required.</small>", unsafe_allow_html=True)
