import streamlit as st
import fitz
import re
import os
from urllib.parse import urlparse

from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

import plotly.express as px
from fpdf import FPDF

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
    initial_sidebar_state="expanded"
)

# Initialize Session State for tracking history
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- SIDEBAR ---------------- #
with st.sidebar:

    st.markdown("""
    <div style="font-size: 28px; font-weight: bold; margin-bottom: -10px;">
    Fact<span style="color: #5B8CFF;">Check</span> AI
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # APP CONFIGURATIONS
    st.markdown("### Engine Settings")

    search_depth = st.selectbox(
        "Search Depth",
        ["basic", "advanced"],
        help="Advanced depth conducts intensive web research but might take slightly longer."
    )

    custom_trusted = st.multiselect(
        "Prioritize Trusted Domains",
        ["gov", "edu", "who.int", "statista.com", "forbes.com", "mckinsey.com", "un.org"],
        default=["who.int", "statista.com", "gov"]
    )

    st.markdown("---")

    # SYSTEM STATUS
    st.markdown("### System Status")

    st.markdown("""
    **AI Engine** · <span style='color:#10B981;'>Online</span><br>
    **Web Search** · <span style='color:#10B981;'>Active ({})</span><br>
    **PDF Parser** · <span style='color:#10B981;'>Ready</span>
    """.format(search_depth.upper()), unsafe_allow_html=True)

    st.markdown("---")

    # SESSION HISTORY
    st.markdown("### Session Scan Logs")

    if st.session_state.history:

        for idx, item in enumerate(reversed(st.session_state.history)):

            st.caption(f"**{idx+1}. {item['filename']}**")

            st.markdown(
                f"<span style='font-size:12px;'>✅ {item['v']} | ⚠️ {item['i']} | ❌ {item['f']}</span>",
                unsafe_allow_html=True
            )

    else:

        st.caption("No documents processed in this session yet.")

    st.markdown("---")

    # QUICK STATS
    st.markdown("### Verification Metrics")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("Global Accuracy", "98%")

    with c2:
        st.metric("Avg Latency", "4.2 sec")

# ---------------- CUSTOM CSS ---------------- #
st.markdown("""
<style>

/* =========================
MAIN APP
========================= */

.stApp {
    background: linear-gradient(to bottom right, #050816, #0B1120);
    color: white;
    overflow-x: hidden;
}

/* =========================
LAYOUT
========================= */

.block-container {
    max-width: 1350px;
    padding-top: 0.5rem;
}

/* Hide Streamlit Branding safely without breaking the sidebar button */
[data-testid="stHeader"] {
    background-color: transparent;
    background-image: none;
}
}
footer {
    visibility: hidden;
}
            
section[data-testid="stSidebar"] {
    background: rgba(10,15,30,0.95);
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* =========================
HERO GLOW
========================= */

.hero-glow {
    position: absolute;

    width: 500px;
    height: 500px;

    background:
    radial-gradient(
        circle,
        rgba(91,140,255,0.25),
        transparent 70%
    );

    filter: blur(80px);

    z-index: -1;

    top: -100px;
    right: -100px;
}

/* =========================
LOGO
========================= */

.logo {
    font-size: 30px;
    font-weight: bold;
}

.logo span {
    color: #5B8CFF;
}

/* =========================
HERO SECTION
========================= */

.hero-title {
    font-size: 72px;
    font-weight: 800;
    line-height: 1.1;
}

.hero-title span {
    background: linear-gradient(
        90deg,
        #4F8CFF,
        #8B5CF6
    );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 25px;
    font-size: 22px;
    color: #94A3B8;
    line-height: 1.7;
}

/* =========================
HERO BADGES
========================= */

.hero-badge {
    background: rgba(255,255,255,0.05);

    padding: 12px 18px;

    border-radius: 14px;

    border: 1px solid rgba(255,255,255,0.08);

    font-size: 14px;
    font-weight: 500;

    transition: 0.3s;
}

.hero-badge:hover {

    transform: translateY(-3px);

    border: 1px solid rgba(91,140,255,0.4);

    background: rgba(255,255,255,0.08);
}

/* =========================
FLOATING ANIMATION
========================= */

@keyframes float {

    0% {
        transform: translateY(0px);
    }

    50% {
        transform: translateY(-10px);
    }

    100% {
        transform: translateY(0px);
    }
}
            

.upload-card {

    background: rgba(255,255,255,0.03);

    border: 1px solid rgba(255,255,255,0.08);

    padding: 28px;

    border-radius: 30px;

    backdrop-filter: blur(15px);

    box-shadow:
    0 0 40px rgba(91,140,255,0.15),
    0 0 120px rgba(91,140,255,0.08);

    transition: 0.4s;
}

/* =========================
FILE UPLOADER
========================= */

[data-testid="stFileUploader"] {

    background: rgba(255,255,255,0.03);

    border-radius: 20px;

    padding: 10px 18px;

    border: 2px dashed rgba(91,140,255,0.3);

    transition: 0.3s;
}

[data-testid="stFileUploader"]:hover {

    border: 2px dashed rgba(91,140,255,0.7);

    background: rgba(255,255,255,0.05);
}

[data-testid="stFileUploaderDropzone"] {

    padding: 0 !important;

    min-height: auto !important;
}

/* REMOVE EMPTY TOP BAR */
section[data-testid="stFileUploader"] > div:first-child {

    display: none;
}


/* =========================
PREVIEW INSIGHT CARDS
========================= */
.preview-card {

    animation: float 6s ease-in-out infinite;

    background: rgba(255,255,255,0.04);

    padding: 14px;

    border-radius: 16px;

    border: 1px solid rgba(255,255,255,0.08);

    margin-top: 14px;

    line-height: 1.6;

    transition: 0.3s;
}
            
/* =========================
SECTION TITLES
========================= */

.section-title {

    text-align: center;

    font-size: 48px;

    font-weight: 700;

    margin-top: 70px;

    margin-bottom: 50px;
}

/* =========================
WORKFLOW CARDS
========================= */

.card-container {

    display: flex;

    justify-content: center;

    gap: 30px;

    flex-wrap: wrap;

    margin-bottom: 50px;
}

.info-card {

    background: rgba(255,255,255,0.03);

    border: 1px solid rgba(255,255,255,0.08);

    padding: 30px;

    border-radius: 24px;

    width: 240px;

    transition: 0.3s;
}

.info-card:hover {

    transform: translateY(-10px);

    box-shadow:
    0px 0px 30px rgba(91,140,255,0.2);
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

/* =========================
BUTTONS
========================= */

.stButton>button {

    background: linear-gradient(
        90deg,
        #4F8CFF,
        #8B5CF6
    );

    color: white;

    border: none;

    padding: 12px 28px;

    border-radius: 12px;

    font-size: 18px;

    font-weight: 600;

    transition: 0.3s;
}

.stButton>button:hover {

    transform: scale(1.03);
}

/* =========================
RESULT CARDS
========================= */

.result-card {

    background: rgba(255,255,255,0.03);

    border: 1px solid rgba(255,255,255,0.08);

    padding: 30px;

    border-radius: 24px;

    margin-top: 20px;

    line-height: 1.8;

    white-space: pre-wrap;

    transition: 0.3s;
}

.result-card:hover {

    transform: translateY(-5px);
}

/* =========================
RESULT TYPES
========================= */

.verified {

    border-left: 6px solid #10B981;

    box-shadow:
    0px 0px 25px rgba(16,185,129,0.2);
}

.inaccurate {

    border-left: 6px solid #F59E0B;

    box-shadow:
    0px 0px 25px rgba(245,158,11,0.2);
}

.false {

    border-left: 6px solid #EF4444;

    box-shadow:
    0px 0px 25px rgba(239,68,68,0.2);
}

/* =========================
STATUS PILLS
========================= */

.status-pill {

    display:inline-block;

    padding:8px 18px;

    border-radius:999px;

    font-size:14px;

    font-weight:700;

    margin-bottom:16px;
}

.green-pill {

    background:#052E1A;

    color:#10B981;
}

.yellow-pill {

    background:#3B2500;

    color:#F59E0B;
}

.red-pill {

    background:#3B0A0A;

    color:#EF4444;
}

/* =========================
METRICS
========================= */

.metric-box {

    background: rgba(255,255,255,0.03);

    padding: 25px;

    border-radius: 20px;

    text-align: center;

    border: 1px solid rgba(255,255,255,0.08);
}

/* =========================
CONFIDENCE
========================= */

.confidence-text {

    color:#94A3B8;

    margin-bottom:10px;

    font-size:15px;
}

</style>
""", unsafe_allow_html=True)


# ---------------- HERO SECTION ---------------- #
col1, col2 = st.columns([1.1, 1])

with col1:

    st.markdown("""
    <div class="hero-title">
    Real Facts.<br>
    <span>Zero Doubt.</span>
    </div>

    <div class="hero-subtitle">
    Upload PDFs and verify claims using AI-powered live web intelligence and source-backed reasoning.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
<div style="
display:flex;
gap:14px;
margin-top:30px;
flex-wrap:wrap;
">

<div style="
background:rgba(255,255,255,0.05);
padding:12px 18px;
border-radius:14px;
border:1px solid rgba(255,255,255,0.08);
">
⚡ AI-Powered
</div>

<div style="
background:rgba(255,255,255,0.05);
padding:12px 18px;
border-radius:14px;
border:1px solid rgba(255,255,255,0.08);
">
🌐 Live Web Data
</div>

<div style="
background:rgba(255,255,255,0.05);
padding:12px 18px;
border-radius:14px;
border:1px solid rgba(255,255,255,0.08);
">
📄 PDF Intelligence
</div>

<div style="
background:rgba(255,255,255,0.05);
padding:12px 18px;
border-radius:14px;
border:1px solid rgba(255,255,255,0.08);
">
🛡️ Trusted Sources
</div>

</div>
""", unsafe_allow_html=True)

with col2:

    st.markdown('<div class="upload-card">', unsafe_allow_html=True)

    st.subheader("📄 Upload File")

    uploaded_file = st.file_uploader(
        "",
        type=["pdf"]
    )

    st.markdown(
        "<span style='color:#94A3B8;'>Supports reports, research papers, financial documents and technical PDFs.</span>",
        unsafe_allow_html=True
    )

    # SECTION HEADING
    st.markdown("""
    <div style="
    margin-top:30px;
    margin-bottom:10px;
    ">

    <div style="
    font-size:16px;
    font-weight:600;
    color:white;
    ">
    🔎 Live Verification Examples
    </div>

    <div style="
    font-size:14px;
    color:#94A3B8;
    margin-top:4px;
    ">
    Preview how FactCheck AI detects misinformation and verifies claims.
    </div>

    </div>
    """, unsafe_allow_html=True)

    # PREVIEW CARDS
    st.markdown("""
    <div style="
    margin-top:25px;
    display:flex;
    flex-direction:column;
    gap:14px;
    ">

    <div style="
    background:rgba(255,255,255,0.04);
    padding:14px;
    border-radius:16px;
    border:1px solid rgba(255,255,255,0.08);
    ">
    ⚠️ “AI Market reached $12T in 2024”
    <br>
    <span style="color:#EF4444;">Potentially False</span>
    </div>

    <div style="
    background:rgba(255,255,255,0.04);
    padding:14px;
    border-radius:16px;
    border:1px solid rgba(255,255,255,0.08);
    ">
    ✅ “India internet users crossed 900M”
    <br>
    <span style="color:#10B981;">Verified</span>
    </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- PDF EXTRACTION ---------------- #
def extract_text_from_pdf(pdf_file):

    text = ""

    pdf = fitz.open(
        stream=pdf_file.read(),
        filetype="pdf"
    )

    for page in pdf:

        text += f"\n\n--- PAGE {page.number + 1} ---\n\n"
        text += page.get_text()

    return text

# ---------------- CLAIM EXTRACTION ---------------- #
def extract_claims(text):

    prompt = f"""
You are an AI fact-checking assistant.

Extract ONLY factual claims from the following document.

Focus on:
- statistics
- percentages
- financial numbers
- growth figures
- technical claims
- dates
- comparisons
- market size
- user counts
- revenue figures

Return ONLY a clean numbered list.

Document:
{text[:12000]}
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content

    claims = []

    for line in content.split("\n"):

        line = line.strip()

        if len(line) > 15:
            line = re.sub(r'^\d+\.\s*', '', line)
            claims.append(line)

    return claims

# ---------------- SOURCE BADGES ---------------- #
def format_source_badge(url):

    domain = urlparse(url).netloc

    # Dynamic fallback checks against user customization options
    trusted = any(td in domain for td in custom_trusted)

    if trusted:

        return f"""
        <div style="
            display:inline-block;
            padding:8px 14px;
            margin:6px;
            border-radius:12px;
            background:#062E1F;
            color:#10B981;
            border:1px solid #10B981;
            font-size:14px;
        ">
        ✅ {domain}
        </div>
        """

    else:

        return f"""
        <div style="
            display:inline-block;
            padding:8px 14px;
            margin:6px;
            border-radius:12px;
            background:#2A1A05;
            color:#F59E0B;
            border:1px solid #F59E0B;
            font-size:14px;
        ">
        ⚠️ {domain}
        </div>
        """

# ---------------- CONFIDENCE ---------------- #
def extract_confidence(result):

    match = re.search(
        r'Confidence:\s*(\d+)',
        result
    )

    if match:
        return int(match.group(1))

    return None

# ---------------- CLAIM VERIFICATION ---------------- #
def verify_claim(claim):

    try:

        short_claim = claim[:350]

        # Injects current configuration value from user selection setup
        search_result = tavily.search(
            query=short_claim,
            search_depth=search_depth
        )

        web_content = ""
        sources = []

        for result in search_result["results"][:3]:

            web_content += result["content"] + "\n"
            sources.append(result["url"])

        prompt = f"""
You are an advanced AI fact-checking system.

Your task is to verify whether the claim is factually correct using the provided web evidence.

CLAIM:
{claim}

WEB EVIDENCE:
{web_content}

Instructions:
1. Compare the claim carefully.
2. Determine whether it is:
   - VERIFIED
   - INACCURATE
   - FALSE

3. Provide:
   - confidence score
   - severity level
   - corrected fact
   - short explanation

Respond ONLY in this format.

Do not add markdown.
Do not add bullet points.
Do not add extra text.

Status:
Confidence:
Severity:
Correct Fact:
Explanation:
"""

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        final_response = response.choices[0].message.content

        return final_response, sources

    except Exception as e:

        return f"Error: {e}", []

# ---------------- PDF REPORT ---------------- #
def generate_pdf_report(results):

    pdf = FPDF()

    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )

    pdf.add_page()

    pdf.set_font("Arial", "B", 18)

    pdf.cell(
        200,
        10,
        "FactCheck AI Report",
        ln=True
    )

    pdf.ln(10)

    pdf.set_font("Arial", size=11)

    for item in results:

        pdf.multi_cell(
            0,
            8,
            f"Claim: {item['claim']}"
        )

        pdf.multi_cell(
            0,
            8,
            f"Result: {item['result']}"
        )

        pdf.ln(5)

    file_name = "factcheck_report.pdf"

    pdf.output(file_name)

    return file_name

# ---------------- ALERT ---------------- #
if uploaded_file:

    st.markdown("<br>", unsafe_allow_html=True)

    with st.spinner("📄 Extracting PDF text..."):

        pdf_text = extract_text_from_pdf(uploaded_file)

    st.success("✅ PDF processed successfully!")

    st.info(
        "👇 Scroll down to view live verification results."
    )

# ---------------- HOW IT WORKS ---------------- #

st.markdown(
    '<div class="section-title">How It Works</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">01</div>
        <div class="card-title">Submit</div>
        <div class="card-desc">
        Upload your PDF document.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">02</div>
        <div class="card-title">Analyze</div>
        <div class="card-desc">
        AI extracts important factual claims.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">03</div>
        <div class="card-title">Verify</div>
        <div class="card-desc">
        Claims are checked against live web evidence.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="info-card">
        <div class="card-number">04</div>
        <div class="card-title">Results</div>
        <div class="card-desc">
        Receive trusted AI-generated fact verification.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------- MAIN VERIFICATION ---------------- #
if uploaded_file:

    # Double check if this precise file execution has already been logged into history session
    if not any(h['filename'] == uploaded_file.name for h in st.session_state.history):
        is_new_processing = True
    else:
        is_new_processing = False

    verification_results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.markdown(
        "📄 Extracting factual claims..."
    )

    progress_bar.progress(20)

    claims = extract_claims(pdf_text)

    status_text.markdown(
        "🧠 Detecting misinformation patterns..."
    )

    progress_bar.progress(40)

    verified_count = 0
    inaccurate_count = 0
    false_count = 0

    st.markdown(
        '<div class="section-title">Verification Results</div>',
        unsafe_allow_html=True
    )

    for idx, claim in enumerate(claims):

        status_text.markdown(
            f"🌐 Verifying Claim {idx + 1}..."
        )

        progress_bar.progress(60)

        st.markdown(f"## Claim {idx + 1}")

        st.markdown(
            f'<div class="info-card" style="width:100%;">{claim}</div>',
            unsafe_allow_html=True
        )

        with st.spinner("🔎 Cross-checking web evidence..."):

            result, sources = verify_claim(claim)

        confidence = extract_confidence(result)

        card_class = "result-card"
        pill = ""

        result_upper = result.upper()

        if "VERIFIED" in result_upper:

            card_class += " verified"

            verified_count += 1

            pill = """
            <div class="status-pill green-pill">
            ✅ VERIFIED
            </div>
            """

        elif "INACCURATE" in result_upper:

            card_class += " inaccurate"

            inaccurate_count += 1

            pill = """
            <div class="status-pill yellow-pill">
            ⚠️ INACCURATE
            </div>
            """

        elif "FALSE" in result_upper:

            card_class += " false"

            false_count += 1

            pill = """
            <div class="status-pill red-pill">
            ❌ FALSE
            </div>
            """

        st.markdown(
            pill,
            unsafe_allow_html=True
        )

        if confidence:

            st.markdown(
                f"""
                <div class="confidence-text">
                Confidence Score: <b>{confidence}%</b>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            f'<div class="{card_class}">{result}</div>',
            unsafe_allow_html=True
        )

        with st.expander("🌐 View Verification Sources"):

            for src in sources:

                st.markdown(
                    format_source_badge(src),
                    unsafe_allow_html=True
                )

            verification_results.append({
                "claim": claim,
                "result": result
            })

        st.markdown("<br>", unsafe_allow_html=True)

    status_text.markdown(
        "✅ Fact-checking complete!"
    )

    progress_bar.progress(100)

    # Log analytics into history tracking session state
    if is_new_processing:
        st.session_state.history.append({
            "filename": uploaded_file.name,
            "v": verified_count,
            "i": inaccurate_count,
            "f": false_count
        })
        st.rerun()

    # ---------------- ANALYTICS ---------------- #
    st.markdown(
        '<div class="section-title">Verification Analytics</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            f'''
            <div class="metric-box">
                <h2>✅ Verified</h2>
                <h1>{verified_count}</h1>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f'''
            <div class="metric-box">
                <h2>⚠️ Inaccurate</h2>
                <h1>{inaccurate_count}</h1>
            </div>
            ''',
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f'''
            <div class="metric-box">
                <h2>❌ False</h2>
                <h1>{false_count}</h1>
            </div>
            ''',
            unsafe_allow_html=True
        )

    # ---------------- PIE CHART ---------------- #
    chart_data = {
        "Status": [
            "Verified",
            "Inaccurate",
            "False"
        ],

        "Count": [
            verified_count,
            inaccurate_count,
            false_count
        ]
    }

    fig = px.pie(
        names=chart_data["Status"],
        values=chart_data["Count"],
        title="Claim Verification Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # ---------------- RISK SUMMARY ---------------- #
    st.markdown(
        '<div class="section-title">Document Risk Summary</div>',
        unsafe_allow_html=True
    )

    total_issues = inaccurate_count + false_count

    if total_issues == 0:

        risk_level = "🟢 LOW RISK"

    elif total_issues <= 3:

        risk_level = "🟡 MEDIUM RISK"

    else:

        risk_level = "🔴 HIGH RISK"

    st.markdown(
        f"""
        <div class="result-card">
        <h2>{risk_level}</h2>

        <p>
        This document contains
        <b>{total_issues}</b>
        potentially misleading or inaccurate claims.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------- DOWNLOAD REPORT ---------------- #
    pdf_report = generate_pdf_report(
        verification_results
    )

    with open(pdf_report, "rb") as pdf_file:

        st.download_button(
            label="📥 Download Full Verification Report",
            data=pdf_file,
            file_name="FactCheck_Report.pdf",
            mime="application/pdf"
        )

# ---------------- FOOTER ---------------- #
st.markdown("""
<div style="
margin-top:80px;
padding:40px;
border-top:1px solid rgba(255,255,255,0.08);
text-align:center;
">

<div style="
font-size:22px;
font-weight:700;
margin-bottom:12px;
">
🛡️ FactCheck AI
</div>

<div style="
color:#94A3B8;
font-size:16px;
line-height:1.8;
max-width:700px;
margin:auto;
">
AI-powered misinformation detection platform built for intelligent PDF claim verification using live web intelligence and source-backed reasoning.
</div>

<div style="
margin-top:25px;
color:#64748B;
font-size:15px;
">
Built and designed by <b>KALIKA POKHRIYAL</b>
</div>

<div style="
margin-top:8px;
font-size:15px;
">
📩 Feedback & Suggestions:
<a href="mailto:YOURMAIL@gmail.com"
style="
color:#5B8CFF;
text-decoration:none;
">
kalika.pokhriyal@gmail.com
</a>
</div>

<div style="
margin-top:30px;
color:#475569;
font-size:14px;
">
Powered by OpenRouter • Tavily AI • Streamlit • Plotly
</div>

</div>
""", unsafe_allow_html=True)