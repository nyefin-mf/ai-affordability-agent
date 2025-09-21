import streamlit as st
import os



# Page configuration
st.set_page_config(
    page_title="AI Affordability Agent",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 AI Affordability Assessment Agent")
st.markdown("**South African Microfinance NCA Compliance Tool**")

# Initialize the agent
@st.cache_resource
def load_agent():
    return SimpleAffordabilityAgent()

agent = load_agent()

# Create input form
with st.form("affordability_form"):
    st.subheader("Loan Application Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        income = st.number_input("Monthly Income (R)", min_value=0, value=15000)
        expenses = st.number_input("Monthly Expenses (R)", min_value=0, value=8000)
    
    with col2:
        loan_amount = st.number_input("Loan Amount Requested (R)", min_value=0, value=50000)
        loan_term = st.number_input("Loan Term (months)", min_value=1, max_value=72, value=24)
    
    submitted = st.form_submit_button("🔍 Assess Affordability")

# Process the form
if submitted:
    with st.spinner("AI is analyzing the application..."):
        try:
            # Calculate monthly payment estimate
            monthly_payment = loan_amount / loan_term
            
            # Get AI assessment
            assessment = agent.assess_affordability(income, expenses, loan_amount)
            
            # Display results
            st.subheader("📊 Assessment Results")
            
            # Show quick metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                discretionary = income - expenses
                st.metric("Discretionary Income", f"R{discretionary:,.2f}")
            
            with col2:
                st.metric("Estimated Monthly Payment", f"R{monthly_payment:,.2f}")
            
            with col3:
                affordability_ratio = (discretionary / income * 100) if income > 0 else 0
                st.metric("Affordability Ratio", f"{affordability_ratio:.1f}%")
            
            # Show AI analysis
            st.subheader("🤖 AI Analysis")
            st.write(assessment)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Make sure your OpenAI API key is set correctly in the .env file")

# Sidebar info
with st.sidebar:
    st.header("About This Tool")
    st.info("""
    This AI agent helps assess loan affordability according to South African NCA regulations.
    
    **Features:**
    - NCA-compliant calculations
    - AI-powered decision making  
    - Detailed reasoning
    - Real-time assessment
    """)
    
    st.header("NCA Compliance")
    st.warning("""
    This tool provides preliminary assessments only. 
    All decisions must be verified against current NCA regulations.
    """)
