import os

import streamlit as st
from dotenv import load_dotenv

from resume_parser import extract_resume_text
from ai_mentor import get_critique
from pdf_report import generate_pdf

load_dotenv()

st.set_page_config(
    page_title="ATS Resume Auditor & Candid Career Mentor",
    page_icon="🎯",
    layout="wide",
)

# هنا الثيم الجديد الاحترافي (Modern SaaS Theme)
st.markdown(
    """
    <style>
    /* لون الخلفية الأساسي (Slate 900) */
    .stApp { background-color: #0F172A; } 

    /* لون القائمة الجانبية (Slate 800) */
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }

    /* تصميم البانر العلوي */
    .nv-banner {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px 32px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* تصميم الأيقونة داخل البانر */
    .nv-badge {
        flex-shrink: 0;
        width: 56px;
        height: 56px;
        border-radius: 14px;
        background: linear-gradient(135deg, #3B82F6, #2563EB); /* تدرج أزرق ملكي */
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 800;
        font-size: 26px;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    }
    
    /* نصوص البانر */
    .nv-banner h1 {
        color: #F8FAFC;
        font-size: 24px;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .nv-banner p {
        color: #94A3B8;
        margin: 8px 0 0 0;
        font-size: 15px;
        line-height: 1.5;
    }

    /* تصميم الأزرار الأساسية */
    div.stButton > button[kind="primary"],
    .stDownloadButton > button {
        background: linear-gradient(135deg, #3B82F6, #2563EB);
        border: none;
        border-radius: 8px;
        color: #fff;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
    }
    div.stButton > button[kind="primary"]:hover,
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #60A5FA, #3B82F6);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        transform: translateY(-1px);
    }
    
    /* الأزرار الثانوية */
    div.stButton > button[kind="secondary"] {
        background-color: #1E293B;
        border: 1px solid #475569;
        border-radius: 8px;
        color: #F1F5F9;
        transition: all 0.2s ease;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #94A3B8;
        color: #fff;
    }

    /* الصناديق ومنطقة رفع الملفات */
    [data-testid="stExpander"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1E293B;
        border: 2px dashed #475569;
        border-radius: 10px;
        transition: all 0.2s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #3B82F6;
        background-color: #1e293bcf;
    }

    /* حقول الإدخال */
    textarea, input {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
    }
    textarea:focus, input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 1px #3B82F6 !important;
    }

    /* العناوين الجانبية (الأقسام) */
    .stMarkdown h2 {
        background-color: transparent;
        border-left: 4px solid #3B82F6;
        padding: 4px 12px;
        border-radius: 0px;
        color: #F8FAFC;
        font-size: 18px;
        margin-top: 24px;
    }

    /* الخطوط الفاصلة */
    hr { border-color: #334155; }
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
        <div class="nv-badge">🎯</div>
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
            try:
                api_key = st.secrets["ANTHROPIC_API_KEY"]
            except Exception:
                api_key = os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                st.error(
                    "System Error: API Key is missing from the server configuration."
                )
            else:
                with st.spinner("The Candid Mentor is reading your resume... brace yourself."):
                    try:
                        critique = get_critique(st.session_state.resume_text, api_key)
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