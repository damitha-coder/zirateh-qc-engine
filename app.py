import streamlit as st
import os
import json
import time
from datetime import datetime
from google import genai
from google.genai import types
from weasyprint import HTML
import jinja2

# Page layout configurations
st.set_page_config(page_title="Zirateh Video QC Tool", layout="wide", page_icon="🎬")

st.title("🎬 Zirateh Video Compliance & Audit Engine")
st.markdown("Upload your structural media files below to perform frame-by-frame compliance verification checks.")

# Sidebar Configuration for API Authentication
st.sidebar.header("🔧 API Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))

if not api_key:
    st.warning("⚠️ Please provide a valid Gemini API Key in the sidebar or setting environment variables to activate backend tasks.")
    st.stop()

# Initialize Client
client = genai.Client(api_key=api_key)

# Main Form Components
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Context & Rulesets Ingestion")
    brief_input = st.text_area("Paste Content Brief Rules / Page Specifics:", height=150, 
                               placeholder="e.g., Must show prices at the beginning. 5-star ranking graphic layout at the end.")
    checklist_input = st.text_area("Paste QC Checklist Parameter Matrix:", height=150,
                                   placeholder="e.g., Pattern interrupt every 3-5 seconds. Audio levels balanced. Check for text errors.")

with col2:
    st.subheader("📤 Media Asset Upload")
    uploaded_video = st.file_uploader("Choose your edited video file (.mp4, .mov)", type=["mp4", "mov"])

if st.button("🚀 Run Video Compliance Audit", type="primary"):
    if not brief_input or not checklist_input or not uploaded_video:
        st.error("Please fill in all textual guidelines fields and upload a target video asset file before initializing.")
    else:
        # Save uploaded file temporarily to execution paths
        temp_video_path = f"temp_{uploaded_video.name}"
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())

        try:
            with st.spinner("Step 1/3: Exporting video file to Cloud processing space safely..."):
                video_asset = client.files.upload(file=temp_video_path)
                
                # Check frame calculation staging state loops
                while video_asset.state.name == "PROCESSING":
                    time.sleep(8)
                    video_asset = client.files.get(name=video_asset.name)
                
                if video_asset.state.name == "FAILED":
                    st.error("Cloud processing pipeline failed to parse video tracks.")
                    st.stop()

            with st.spinner("Step 2/3: Analyzing frames and cross-referencing timeline structures against rules..."):
                analysis_prompt = f"""
                You are a strict Post-Production Executive and Quality Control Director for short-form video content.
                Analyze the uploaded video file track sequences against the strict structural rules provided.
                
                Content Strategy Brief Rules:
                {brief_input}
                
                Technical QC Checklist Parameters:
                {checklist_input}
                
                You must return your complete response strictly as a structured JSON array matching this exact format:
                [
                  {{
                    "section": "Technical QC",
                    "subsection": "Audio Balance",
                    "status": "Pass",
                    "detail": "Dialogue is prioritized cleanly over background track."
                  }},
                  {{
                    "section": "Copy & Text",
                    "subsection": "Spelling Errors",
                    "status": "Fail",
                    "detail": "Typo detected at 00:16: 'Onx' instead of 'Onyx'."
                  }}
                ]
                Do not wrap the JSON output inside any markdown strings or conversational text headers.
                """

                response = client.models.generate_content(
                    model='gemini-2.5-pro', # Pro framework handles advanced reasoning & multi-minute video contexts smoothly
                    contents=[video_asset, analysis_prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1 # Forces factual alignment without random assumptions
                    ),
                )
                
                # Turn output into structured object array
                json_data = json.loads(response.text)

            with st.spinner("Step 3/3: Rendering PDF report via layout templates..."):
                # Render Jinja Template mapping matching dynamic variables
                template_loader = jinja2.FileSystemLoader(searchpath="./")
                template_env = jinja2.Environment(loader=template_loader)
                template = template_env.get_template("template.html")
                
                html_output = template.render(
                    date=datetime.now().strftime("%B %d, %Y"),
                    filename=uploaded_video.name,
                    matrix=json_data
                )
                
                pdf_filename = "zirateh_output_audit.pdf"
                HTML(string=html_output).write_pdf(pdf_filename)

            st.success("✅ Complete System Check Finalized!")

            # Display on-screen preview table matrix
            st.subheader("📊 Internal Audit Results Preview")
            st.table(json_data)

            # Download Option button
            with open(pdf_filename, "rb") as pdf_file:
                st.download_button(
                    label="📥 Download Structured PDF Audit Sheet",
                    data=pdf_file,
                    file_name=f"Audit_Report_{uploaded_video.name}.pdf",
                    mime="application/pdf"
                )

            # Clean workspace records
            os.remove(pdf_filename)

        except Exception as err:
            st.error(f"Execution Error occurred inside engine workspace: {str(err)}")
        
        finally:
            # Always ensure local media dumps and cloud session keys are cleared to protect operational security
            if 'video_asset' in locals():
                client.files.delete(name=video_asset.name)
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
