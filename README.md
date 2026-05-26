# AI Fact-Checking Web App

An AI-powered fact-checking web application that extracts factual claims from PDF documents and verifies them using live web search and LLM reasoning.

## Features

- Upload PDF documents
- Automatic claim extraction
- AI-powered fact verification
- Live web evidence retrieval
- Source citation support
- Interactive Streamlit UI

## Tech Stack

- Python
- Streamlit
- OpenRouter API
- Tavily Search API
- PyMuPDF

## Live Demo

Deployed on Streamlit Cloud.

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Environment Variables

Create a `.env` file with:

```env
TAVILY_API_KEY=your_key
OPENROUTER_API_KEY=your_key
```

## Author

Kalika Pokhriyal