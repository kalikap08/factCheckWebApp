import streamlit as st
import fitz
import re
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Tavily
tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Streamlit Page
st.set_page_config(page_title="AI Fact Checker", layout="wide")

st.title("🕵️ AI Fact-Checking Web App")
st.write("Upload a PDF and verify claims using live web data.")

# Sidebar
st.sidebar.title("About")
st.sidebar.write("This app extracts factual claims from PDFs and verifies them using AI + live web search.")

# Upload PDF
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

# Extract PDF Text
def extract_text_from_pdf(pdf_file):

    text = ""

    pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")

    for page in pdf:
        text += page.get_text()

    return text

# Extract Claims
def extract_claims(text):

    sentences = re.split(r'(?<=[.!?]) +', text)

    claims = []

    keywords = [
        "%",
        "percent",
        "million",
        "billion",
        "$",
        "USD",
        "growth",
        "revenue",
        "2020",
        "2021",
        "2022",
        "2023",
        "2024",
        "2025"
    ]

    for sentence in sentences:
        if any(keyword.lower() in sentence.lower() for keyword in keywords):
            claims.append(sentence)

    return claims[:10]

# Verify Claims
# Verify Claims
def verify_claim(claim):

    try:

        search_result = tavily.search(
            query=claim,
            search_depth="basic"
        )

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

Respond ONLY in this format:

Status:
Correct Info:
Explanation:
"""

        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        final_response = response.choices[0].message.content

        source_text = "\n\nSources:\n"

        for src in sources:
            source_text += f"- {src}\n"

        return final_response + source_text

    except Exception as e:

        return f"Error: {e}"
    
# Main Logic
if uploaded_file:

    with st.spinner("Extracting PDF text..."):

        pdf_text = extract_text_from_pdf(uploaded_file)

    st.success("PDF processed successfully!")

    claims = extract_claims(pdf_text)

    st.metric("Claims Found", len(claims))

    st.divider()

    st.subheader("Extracted Claims & Verification")

    for idx, claim in enumerate(claims):

        st.markdown(f"## Claim {idx+1}")

        st.write(claim)

        with st.spinner("Verifying claim..."):

            result = verify_claim(claim)

        if "Verified" in result:
            st.success(result)

        elif "Inaccurate" in result:
            st.warning(result)

        elif "False" in result:
            st.error(result)

        else:
            st.info(result)

        st.divider()