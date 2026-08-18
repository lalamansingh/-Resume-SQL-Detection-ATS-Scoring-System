import streamlit as st
import os
import tempfile
import json
from resume_parser import parse_resume
from sql_injection_detector import SQLInjectionDetector
from ats_scorer import ATSScorer

# Set page config
st.set_page_config(
    page_title="Resume SQL Detection & ATS Scorer",
    page_icon="📄",
    layout="wide"
)

# Title and description
st.title("📄 Resume SQL Detection & ATS Scoring System")
st.markdown("""
This application helps you:
1. **Detect SQL injection attempts** in resume files
2. **Sanitize resumes** by removing malicious patterns
3. **Calculate ATS scores** to see how well your resume would perform in Applicant Tracking Systems
""")

# Sidebar for options
st.sidebar.header("Options")
sanitize_option = st.sidebar.checkbox(
    "Sanitize SQL injection (remove detected patterns)",
    value=True,
    help="If checked, detected SQL injection patterns will be removed from the resume text before scoring"
)

# File upload section
st.header("📁 Upload Files")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Resume File")
    resume_file = st.file_uploader(
        "Upload your resume (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        key="resume_upload"
    )

with col2:
    st.subheader("Job Description (Optional)")
    job_desc_file = st.file_uploader(
        "Upload job description for better ATS scoring (TXT)",
        type=["txt"],
        key="job_desc_upload"
    )

# Process button
if st.button("🔍 Analyze Resume", type="primary"):
    if resume_file is None:
        st.error("Please upload a resume file.")
    else:
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp_resume:
            tmp_resume.write(resume_file.getvalue())
            resume_path = tmp_resume.name

        job_desc_path = None
        if job_desc_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w') as tmp_job:
                tmp_job.write(job_desc_file.getvalue().decode('utf-8'))
                job_desc_path = tmp_job.name

        try:
            # Parse resume
            with st.spinner("Extracting text from resume..."):
                resume_text = parse_resume(resume_path)

            # Display extracted text in an expander
            with st.expander("📄 View Extracted Resume Text"):
                st.text_area("Resume Content", resume_text, height=200, disabled=True)

            # SQL Injection Detection
            with st.spinner("Checking for SQL injection..."):
                detector = SQLInjectionDetector()
                is_malicious, matches = detector.detect(resume_text)

            # Display SQL injection results
            st.header("🔒 SQL Injection Analysis")
            if is_malicious:
                st.error(f"⚠️ **SQL Injection Detected!** Found {len(matches)} suspicious pattern(s).")
                with st.expander("View Detected Patterns"):
                    for i, match in enumerate(matches, 1):
                        st.write(f"{i}. `{match}`")

                if sanitize_option:
                    with st.spinner("Sanitizing resume..."):
                        sanitized_text = detector.sanitize(resume_text)
                    text_to_score = sanitized_text
                    st.info("🧹 Resume has been sanitized (SQL injection patterns removed).")

                    # Show comparison
                    with st.expander("View Sanitized Text"):
                        st.text_area("Sanitized Content", sanitized_text, height=200, disabled=True)
                else:
                    text_to_score = resume_text
                    st.warning("⚠️ SQL injection detected but NOT sanitized (as per your settings).")
            else:
                st.success("✅ **No SQL injection detected.** Your resume appears to be clean.")
                text_to_score = resume_text

            # ATS Scoring
            with st.spinner("Calculating ATS score..."):
                job_description = None
                if job_desc_path and os.path.exists(job_desc_path):
                    with open(job_desc_path, 'r', encoding='utf-8') as f:
                        job_description = f.read()

                scorer = ATSScorer()
                scores = scorer.score_resume(text_to_score, job_description)

            # Display ATS scores
            st.header("📊 ATS Scoring Results")

            # Create columns for metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="Section Presence",
                    value=f"{scores['section_presence']:.0%}",
                    help="Score based on presence of standard resume sections (contact, experience, education, skills, summary)"
                )

            with col2:
                st.metric(
                    label="Keyword Density",
                    value=f"{scores['keyword_density']:.0%}",
                    help="Score based on density of ATS-relevant keywords"
                )

            with col3:
                st.metric(
                    label="Length Score",
                    value=f"{scores['length']:.0%}",
                    help="Score based on resume length (ideal around 400-800 words)"
                )

            if 'semantic_similarity' in scores:
                with col4:
                    st.metric(
                        label="Job Match",
                        value=f"{scores['semantic_similarity']:.0%}",
                        help="Semantic similarity between resume and job description"
                    )

            # Overall score
            overall_percentage = scores['overall'] * 100
            st.subheader("Overall ATS Score")
            st.progress(scores['overall'])
            st.markdown(f"### {overall_percentage:.1f}%")

            # Interpretation
            if overall_percentage >= 80:
                st.success("🎉 Excellent! Your resume is well-optimized for ATS systems.")
            elif overall_percentage >= 60:
                st.info("👍 Good! Your resume should pass most ATS screenings.")
            elif overall_percentage >= 40:
                st.warning("⚠️ Fair. Consider improving your resume for better ATS compatibility.")
            else:
                st.error("❌ Poor. Your resume may struggle to pass ATS filters. Consider revising.")

            # Detailed scores
            with st.expander("📈 Detailed Scores"):
                st.json(scores)

            # Download results
            results = {
                "resume_file": resume_file.name,
                "sql_injection_detected": is_malicious,
                "sql_injection_matches": matches,
                "sanitized": sanitize_option and is_malicious,
                "ats_scores": scores,
                "ats_score_percentage": overall_percentage
            }

            st.download_button(
                label="💾 Download Results as JSON",
                data=json.dumps(results, indent=2),
                file_name="resume_analysis_results.json",
                mime="application/json"
            )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)

        finally:
            # Clean up temporary files
            try:
                os.unlink(resume_path)
                if job_desc_path and os.path.exists(job_desc_path):
                    os.unlink(job_desc_path)
            except:
                pass

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit | For educational purposes only</p>
</div>
""", unsafe_allow_html=True)