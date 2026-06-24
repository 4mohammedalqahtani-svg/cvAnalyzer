import os

import streamlit as st
from dotenv import load_dotenv

from resume_parser import extract_resume_text
from ai_mentor import get_critique
from pdf_report import generate_pdf

load_dotenv()

st.set_page_config(
    page_title="ATS Resume Auditor & Candid Career Mentor",
    page_icon="📄",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0A0A12; }

    [data-testid="stSidebar"] {
        background-color: #0D0D16;
        border-right: 1px solid #1F1F2E;
    }

    .nv-banner {
        background: linear-gradient(135deg, #14101F 0%, #1D1530 55%, #261A3D 100%);
        border: 1px solid #2A2240;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 18px;
    }
    .nv-badge {
        flex-shrink: 0;
        width: 52px;
        height: 52px;
        border-radius: 12px;
        background: linear-gradient(135deg, #7C3AED, #A855F7);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 800;
        font-size: 22px;
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.45);
    }
    .nv-banner h1 {
        color: #FFFFFF;
        font-size: 26px;
        margin: 0;
        font-weight: 700;
    }
    .nv-banner p {
        color: #9295A6;
        margin: 6px 0 0 0;
        font-size: 14.5px;
    }

    div.stButton > button[kind="primary"],
    .stDownloadButton > button {
        background: linear-gradient(135deg, #7C3AED, #9333EA);
        border: none;
        border-radius: 10px;
        color: #fff;
        font-weight: 600;
        padding: 0.55rem 1.3rem;
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35);
    }
    div.stButton > button[kind="primary"]:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #8B4EFF, #A855F7);
        color: #fff;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #14141F;
        border: 1px solid #2A2A3D;
        border-radius: 10px;
        color: #E5E5F0;
    }

    [data-testid="stExpander"] {
        background-color: #101018;
        border: 1px solid #1F1F2E;
        border-radius: 12px;
    }

    [data-testid="stFileUploaderDropzone"] {
        background-color: #101018;
        border: 1px dashed #2A2A3D;
        border-radius: 12px;
    }

    textarea, input {
        background-color: #101018 !important;
        color: #E5E5F0 !important;
        border: 1px solid #2A2A3D !important;
        border-radius: 8px !important;
    }

    .stMarkdown h2 {
        background-color: #14101F;
        border-left: 4px solid #8B5CF6;
        padding: 10px 14px;
        border-radius: 8px;
        color: #FFFFFF;
        font-size: 16px;
        margin-top: 22px;
    }

    hr { border-color: #1F1F2E; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "critique" not in st.session_state:
    st.session_state.critique = None
if "resume_text" not in st.session_state:
    st.session_state.resume_text = None
if "filename" not in st.session_state:
    st.session_state.filename = None

st.markdown(
    """
    <div class="nv-banner">
        <div class="nv-badge">📄</div>
        <div>
            <h1>ATS Resume Auditor & Candid Career Mentor</h1>
            <p>Brutally honest, zero-fluff resume feedback. We will never rewrite a single
            word of your resume for you - only tell you exactly what's wrong and why.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Settings")
    env_key = os.getenv("ANTHROPIC_API_KEY", "")
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=env_key,
        type="password",
        help="Loaded from your .env file if present. You can override it here for this session only.",
    )
    candidate_name = st.text_input(
        "Your name (optional, used only in the PDF report header)", value=""
    )
    st.divider()
    st.markdown(
        "**How it works**\n\n"
        "1. Upload your resume (PDF, DOCX, or TXT)\n"
        "2. Click 'Run Audit'\n"
        "3. Read the unfiltered critique\n"
        "4. Download it as a PDF report\n\n"
        "Your resume content is sent to the Anthropic API solely to generate the "
        "critique and is not stored by this app."
    )

uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    try:
        resume_text = extract_resume_text(uploaded_file.name, file_bytes)
        st.session_state.resume_text = resume_text
        st.session_state.filename = uploaded_file.name
    except Exception as exc:
        st.error(f"Failed to read your resume: {exc}")
        st.session_state.resume_text = None

    if st.session_state.resume_text:
        with st.expander("Preview extracted resume text"):
            st.text_area(
                "Extracted text", st.session_state.resume_text, height=250, disabled=True
            )

        run_audit = st.button("Run Audit", type="primary")

        if run_audit:
            if not api_key_input:
                st.error(
                    "Please provide an Anthropic API key in the sidebar or in your "
                    ".env file before running the audit."
                )
            else:
                with st.spinner("The Candid Mentor is reading your resume... brace yourself."):
                    try:
                        critique = get_critique(st.session_state.resume_text, api_key_input)
                        st.session_state.critique = critique
                    except Exception as exc:
                        st.session_state.critique = None
                        st.error(f"The audit failed: {exc}")

if st.session_state.critique:
    st.divider()
    st.subheader("Your Audit Results")
    st.markdown(st.session_state.critique)

    pdf_bytes = generate_pdf(st.session_state.critique, candidate_name=candidate_name)
    report_filename = "resume_audit_report.pdf"
    if st.session_state.filename:
        base_name = os.path.splitext(st.session_state.filename)[0]
        report_filename = f"{base_name}_audit_report.pdf"

    st.download_button(
        label="Download Critique as PDF",
        data=pdf_bytes,
        file_name=report_filename,
        mime="application/pdf",
        type="primary",
    )
