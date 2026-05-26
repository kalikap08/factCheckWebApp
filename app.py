import streamlit as st
import fitz
import re
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
import os

# ---------------- LOAD ENV ---------------- #
load_dotenv()

# ---------------- API CONFIG ---------------- #
tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY") or st.secrets["TAVILY_API_KEY"]
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY") or st.secrets["OPENROUTER_API_KEY"],
)

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(
    page_title="FactCheck AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CUSTOM CSS ---------------- #
st.markdown("""
<style>

/* Main App */
.stApp {
    background: linear-gradient(to bottom right, #050816, #0B1120);
    color: white;
    overflow-x: hidden;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Navbar */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 60px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

.logo {
    font-size: 30px;
    font-weight: bold;
}

.logo span {
    color: #5B8CFF;
}

/* Hero Section */
.hero {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 80px 60px;
    gap: 50px;
}

/* Hero Left */
.hero-text {
    flex: 1;
}

.hero-title {
    font-size: 72px;
    font-weight: 800;
    line-height: 1.1;
}

.hero-title span {
    background: linear-gradient(90deg, #4F8CFF, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 25px;
    font-size: 24px;
    color: #94A3B8;
    line-height: 1.6;
}

/* Upload Card Wrapper Fixed */
.upload-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 40px;
    border-radius: 30px;
    backdrop-filter: blur(15px);
    box-shadow: 0px 0px 40px rgba(91,140,255,0.15);
}

/* Workflow Section */
.section-title {
    text-align: center;
    font-size: 48px;
    font-weight: 700;
    margin-top: 60px;
    margin-bottom: 50px;
}

/* Cards */
.card-container {
    display: flex;
    justify-content: center;
    gap: 30px;
    padding: 0px 40px 60px 40px;
    flex-wrap: wrap;
}

.info-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 35px;
    border-radius: 24px;
    width: 250px;
    transition: 0.3s;
}

.info-card:hover {
    transform: translateY(-10px);
    box-shadow: 0px 0px 30px rgba(91,140,255,0.2);
}

.card-number {
    font-size: 20px;
    color: #5B8CFF;
    font-weight: bold;
}

.card-title {
    font-size: 28px;
    margin-top: 20px;
    margin-bottom: 15px;
    font-weight: 700;
}

.card-desc {
    color: #94A3B8;
    line-height: 1.6;
}

/* Upload Box */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02);
    border-radius: 20px;
    padding: 30px;
    border: 2px dashed rgba(255,255,255,0.1);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #4F8CFF, #8B5CF6);
    color: white;
    border: none;
    padding: 12px 28px;
    border-radius: 12px;
    font-size: 18px;
    font-weight: 600;
}

/* Result Cards - Added pre-wrap and explicit list squashing rules */
.result-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 30px;
    border-radius: 24px;
    margin-top: 20px;
    line-height: 1.8;
    white-space: pre-wrap; 
}

/* Remove extra gap between markdown list items specifically inside results */
.result-card ul {
    margin-top: 5px !important;
    margin-bottom: 5px !important;
    padding-left: 20px !important;
}

.result-card li {
    margin-bottom: 6px !important;
    line-height: 1.4 !important;
}

.verified {
    border-left: 6px solid #10B981;
    box-shadow: 0px 0px 25px rgba(16,185,129,0.2);
}

.inaccurate {
    border-left: 6px solid #F59E0B;
    box-shadow: 0px 0px 25px rgba(245,158,11,0.2);
}

.false {
    border-left: 6px solid #EF4444;
    box-shadow: 0px 0px 25px rgba(239,68,68,0.2);
}

/* Metrics */
.metric-box {
    background: rgba(255,255,255,0.03);
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
}

</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ---------------- #
st.markdown("""
<div class="navbar">
    <div class="logo">
    🛡️ Fact<span>Check</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- HERO SECTION ---------------- #
col1, col2 = st.columns([1.1, 1])

with col1:
    st.markdown("""
    <div class="hero-text">
        <div class="hero-title">
        Real Facts.<br>
        <span>Zero Doubt.</span>
        </div>
        <div class="hero-subtitle">
        Upload PDFs and verify claims using AI-powered live web intelligence and source-backed reasoning.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    st.subheader("📄 Upload File")
    
    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type=["pdf"],
        label_visibility="collapsed"
    )
    
    st.markdown(
        "<span style='color: #94A3B8; font-size: 14px;'>Supports research papers, reports, and factual documents.</span>", 
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------- PDF PROCESSING LOGIC ---------------- #
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text

def extract_claims(text):
    sentences = re.split(r'(?<=[.!?]) +', text)
    claims = []
    keywords = [
        "%", "percent", "million", "billion", "$", "USD", 
        "growth", "revenue", "2020", "2021", "2022", 
        "2023", "2024", "2025", "2026"
    ]
    for sentence in sentences:
        if any(keyword.lower() in sentence.lower() for keyword in keywords):
            claims.append(sentence)
            
    return claims


def verify_claim(claim):
    try:
        short_claim = claim[:350]
        search_result = tavily.search(query=short_claim, search_depth="basic")
        web_content = ""
        sources = []
        for result in search_result["results"][:3]:
            web_content += result["content"] + "\n"
            sources.append(result["url"])

        prompt = f"""
You are a professional fact checker.

Claim:
{claim}

Web Evidence:
{web_content}

Determine whether the claim is:
- Verified
- Inaccurate
- False

Also provide:
- Correct information
- Short explanation

Respond ONLY in this format, making sure each item starts on a brand new line:

Status: 
Correct Info: 
Explanation: 
"""
        
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        final_response = response.choices[0].message.content
        source_text = "\n\n### Sources:\n"
        for src in sources:
            source_text += f"- {src}\n"
        return final_response + source_text
    except Exception as e:
        return f"Error: {e}"


# --- ALERTS RENDERED ABOVE "HOW IT WORKS" --- #
if uploaded_file:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.spinner("📄 Extracting PDF text..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
    
    st.success("✅ PDF processed successfully!")
    st.info("👇 **Scroll down to view live claim verification results.**")

# ---------------- HOW IT WORKS SECTION ---------------- #
st.markdown(
    '<div class="section-title">How It Works</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="card-container">
    <div class="info-card">
        <div class="card-number">01</div>
        <div class="card-title">Submit</div>
        <div class="card-desc">Upload your PDF or document for fact-checking.</div>
    </div>
    <div class="info-card">
        <div class="card-number">02</div>
        <div class="card-title">Analyze</div>
        <div class="card-desc">AI extracts factual claims and important statements.</div>
    </div>
    <div class="info-card">
        <div class="card-number">03</div>
        <div class="card-title">Verify</div>
        <div class="card-desc">Claims are cross-checked using live web evidence.</div>
    </div>
    <div class="info-card">
        <div class="card-number">04</div>
        <div class="card-title">Results</div>
        <div class="card-desc">Get verified explanations with trusted sources.</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------- VERIFICATION DYNAMIC RUNNER ---------------- #
if uploaded_file:
    claims = extract_claims(pdf_text)
    verified_count = 0
    inaccurate_count = 0
    false_count = 0

    st.markdown('<div class="section-title">Verification Results</div>', unsafe_allow_html=True)

    for idx, claim in enumerate(claims):
        st.markdown(f"## Claim {idx + 1}")
        st.markdown(f'<div class="info-card" style="width:100%;">{claim}</div>', unsafe_allow_html=True)

        with st.spinner("🔎 Verifying claim..."):
            result = verify_claim(claim)

        card_class = "result-card"
        if "Verified" in result:
            card_class += " verified"
            verified_count += 1
        elif "Inaccurate" in result:
            card_class += " inaccurate"
            inaccurate_count += 1
        elif "False" in result:
            card_class += " false"
            false_count += 1

        st.markdown(f'<div class="{card_class}">{result}</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- ANALYTICS ---------------- #
    st.markdown('<div class="section-title">Verification Analytics</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f'<div class="metric-box"><h2>✅ Verified</h2><h1>{verified_count}</h1></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><h2>⚠️ Inaccurate</h2><h1>{inaccurate_count}</h1></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><h2>❌ False</h2><h1>{false_count}</h1></div>', unsafe_allow_html=True)

# ---------------- FOOTER ---------------- #
st.markdown("""
<div style="text-align:center; padding:40px; color:#64748B;">
Built with ❤️ using Streamlit + OpenRouter + Tavily AI
</div>
""", unsafe_allow_html=True)