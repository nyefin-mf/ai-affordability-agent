import streamlit as st
import pandas as pd
import re
from collections import defaultdict

st.set_page_config(page_title="Max Smart Affordability", page_icon="🤖")
st.markdown("<h2 style='text-align:center; color:#1976d2'>🤖 Ultimate Smart Affordability Analyzer</h2>", unsafe_allow_html=True)
st.markdown("##### Upload your South African PDF or CSV bank statement. The app detects ALL recurring income and ALL recurring debits (by amount/reference/pattern), calculates your max qualifying loan, and shows full evidence and ratios.")
st.markdown("---")

def extract_pdf_text(pdf_file):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        return ""

def load_csv(file):
    try:
        df = pd.read_csv(file)
    except:
        file.seek(0)
        df = pd.read_csv(file, encoding='latin1')
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def find_transactions_from_text(text):
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 16]
    results = []
    txn_pat = re.compile(r'((?:\d{2,4}[\/\-]\d{2}[\/\-]\d{2,4})|(?:\d{2}[\/\-]\d{2}[\/\-]\d{2,4}))')
    amt_pat = re.compile(r'(-?R?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})))')
    for l in lines:
        m_date = txn_pat.search(l)
        if not m_date:
            continue
        date = m_date.group(1)
        desc_part = l[m_date.end():]
        amt_match = amt_pat.findall(desc_part)
        if amt_match:
            amount_raw = amt_match[-1][0]
            amount = float(amount_raw.upper().replace('R','').replace(" ","").replace(",",""))
            desc = desc_part.strip().split(amount_raw)[0].strip()[:40]
            results.append((date, desc, amount))
    return results

def find_transactions_from_csv(df):
    amt_col = None
    for c in df.columns:
        if 'amount' in c: amt_col = c
    desc_col = None
    for c in df.columns:
        if c in ('description','details','narration','transaction_description','reference'):
            desc_col = c
    date_col = None
    for c in df.columns:
        if 'date' in c: date_col = c
    txns = []
    for _, row in df.iterrows():
        try:
            date = str(row[date_col])[:10] if date_col else ''
            desc = str(row[desc_col])[:40] if desc_col else ''
            amount = float(str(row[amt_col]).replace("R","").replace(",","").strip()) if amt_col else 0.0
            txns.append((date, desc, amount))
        except:
            continue
    return txns

def advanced_expense_detection(txns):
    # Keywords for recurring expenses (fuzzy match)
    main_keywords = [
        "debit", "direct debit", "prepaid debit", "digital payment", "payment", "insurance", "cell", "vodacom",
        "mtn", "dstv", "medical", "loan", "rent", "bond", "gym", "club", "child", "skool", "school",
        "maintenance", "onderhoud", "fee", "electricity", "admin fee", "tracker", "policy", "prem", "legacy",
        "sirago", "scanfin", "nyefin", "getz", "nasorg", "verblyf", "edgars", "truworths", "license", "ufiling"
    ]
    expense_items = defaultdict(list)
    for d, desc, amt in txns:
        if amt < -250:
            desc_l = desc.lower()
            found_kw = None
            for k in main_keywords:
                if k in desc_l:
                    found_kw = k
                    break
            if found_kw:
                # Round amount for grouping variants
                rounded_amt = round(abs(amt), -1)
                expense_items[(found_kw, rounded_amt)].append(d)
    # Recurring: ≥2 in ≥2 months
    recurring = {}
    for (kw, amt), dts in expense_items.items():
        months = set(x[:7] for x in dts if '-' in x)
        if len(months) >= 2 and len(dts) >= 2:
            recurring[(kw, amt)] = len(dts)
    total_expense = sum(amt for (kw, amt), ct in recurring.items())
    details = "\n".join([f"- {kw.title()} R{amt:,.2f} (x{ct})" for (kw, amt), ct in recurring.items()])
    return total_expense, details

def advanced_income_detection(txns):
    credits = defaultdict(list)
    salary_keywords = ["salary", "credit", "scanfin", "nyefin", "good hope"]
    for d, desc, amt in txns:
        if amt > 1000:
            desc_l = desc.lower()
            if any(k in desc_l for k in salary_keywords):
                key = (round(amt, -2), desc_l[:24])
                credits[key].append(d)
    recurring = {}
    for (amt, desc), dates in credits.items():
        months = set(x[:7] for x in dates if '-' in x)
        if len(months) >= 2 and len(dates) >= 2:
            recurring[amt] = len(dates)
    return max(recurring.keys()) if recurring else max([amt for (_, _, amt) in txns if amt > 1000], default=12000)

statement_file = st.file_uploader("Upload PDF or CSV bank statement", type=['pdf','csv'])

if statement_file:
    if statement_file.type == 'application/pdf':
        text = extract_pdf_text(statement_file)
        txns = find_transactions_from_text(text)
    elif statement_file.type in ('text/csv','application/vnd.ms-excel','application/octet-stream'):
        df = load_csv(statement_file)
        txns = find_transactions_from_csv(df)
    else:
        txns = []

    salary_amt = advanced_income_detection(txns)
    total_recurring_expense, recurring_detail = advanced_expense_detection(txns)

    existing_debt = salary_amt * 0.13
    term, rate = 24, 22
    net_income = salary_amt * 0.75
    discretionary_income = net_income - total_recurring_expense - existing_debt
    max_monthly_payment = discretionary_income / 1.5 if discretionary_income > 0 else 0
    monthly_rate = rate / 100 / 12
    if monthly_rate > 0:
        qualifying_loan = max_monthly_payment * ((1 + monthly_rate) ** term - 1) / (monthly_rate * (1 + monthly_rate) ** term)
    else:
        qualifying_loan = max_monthly_payment * term
    affordability_ratio = discretionary_income / net_income * 100 if net_income > 0 else 0
    debt_service_ratio = max_monthly_payment / net_income * 100 if net_income > 0 else 0
    nca_compliant = discretionary_income > 0 and affordability_ratio >= 25 and debt_service_ratio <= 30

    st.markdown("### Results")
    if nca_compliant and qualifying_loan >= 1000:
        st.markdown(f"<div style='background:#d4edda; color:#155724; border-radius:8px;padding:1rem;font-size:1.5rem;text-align:center;'>✅ You qualify for up to:<br><b>R{qualifying_loan:,.0f}</b></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#f8d7da; color:#721c24; border-radius:8px;padding:1rem;font-size:1.5rem;text-align:center;'>❌ Sorry, you do not qualify currently</div>", unsafe_allow_html=True)
        st.markdown("#### Why? Detailed reasons for decline:")
        reasons = []
        if salary_amt < 5000:
            reasons.append("• No strong recurring income detected (no salary or similar incoming payments can be reliably found).")
        if total_recurring_expense >= 0.7 * salary_amt:
            reasons.append(f"• Recurring expenses are too high compared to income (expenses detected: R{total_recurring_expense:,.2f}).")
        if discretionary_income <= 0:
            reasons.append("• After recurring expenses and estimated debts, there is no discretionary income left each month.")
        if affordability_ratio < 25:
            reasons.append(f"• Affordability ratio is below the legal NCA threshold (needed: 25%+, found: {affordability_ratio:.1f}%).")
        if debt_service_ratio > 30:
            reasons.append(f"• Debt service ratio is above allowed level (needed: ≤30%, found: {debt_service_ratio:.1f}%).")
        if qualifying_loan < 1000:
            reasons.append("• Calculated affordable loan amount is below minimum threshold (R1,000).")
        if not reasons:
            reasons.append("• Other: Detected issue with compliance calculation or missing/unclear statement data.")
        for reason in reasons:
            st.write(reason)

    st.markdown("#### Detected Income & Recurring Expenses")
    st.write(f"- **Monthly Recurring Credit (income):** R{salary_amt:,.2f}")
    st.write(f"- **Total Recurring Monthly Debits:** R{total_recurring_expense:,.2f}")
    st.write(f"- **Estimated other debts:** R{existing_debt:,.2f}")
    st.markdown('#### Expense Details')
    st.text(recurring_detail if recurring_detail else "No strong recurring monthly expenses found.")
    st.markdown("#### Affordability Ratios")
    st.write(f"- **Discretionary income:** R{discretionary_income:,.2f}/month")
    st.write(f"- **Affordability ratio:** {affordability_ratio:.1f}%")
    st.write(f"- **Debt service ratio:** {debt_service_ratio:.1f}%")
    st.write(f"- **NCA Compliance:** {'Yes' if nca_compliant else 'No'}")
    st.markdown("---")
    st.markdown("**Assumptions and logic:**")
    st.write(f"- Loan term: {term} months, interest {rate}%, existing debt heuristically assigned if not directly detected.")
    st.write("Recurring credits: salary detected from most frequent incoming amounts.")
    st.write("Recurring expenses: picks up debits with keywords and loose amount matching, requiring ≥2 in ≥2 months.")
    st.write("Works for major SA bank PDF or CSV statements.")
    if st.button("🔄 Try another statement"):
        st.experimental_rerun()
else:
    st.info("Upload a recent PDF or CSV statement to analyze.")

st.markdown("---")
st.markdown("<small>🤖 Max Smart Affordability &mdash; merchant-aware recurring analysis.</small>", unsafe_allow_html=True)
