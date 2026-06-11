import streamlit as st
from google import genai
from google.genai import types
import json
import os
import time
from weasyprint import HTML
import tempfile

# 1. PERMANENT QC CHECKLIST MATRIX
STANDARD_QC_CHECKLIST = """
1. Technical QC - Audio Balance: Verify dialogue track takes priority cleanly over background music audio. Audio levels must remain balanced without distortion or clipping.
2. Structure - Hook Mechanics: Ensure an explicit visual pattern interrupt, text animation, or thematic hook triggers within the first 3 to 5 seconds of the video timeline to capture viewer retention.
3. Copy & Text - Typography Check: Perform frame-by-frame text inspection to identify any spelling errors, typos, missing punctuation, or awkward line breaks across burned-in subtitles and lower-third graphics.
4. Compliance - Mandatory Visuals: Verify that required branding elements, project pricing models, or official legal disclaimers appear visibly at designated timestamp brackets outlined in the project brief.
5. Pacing - Flow Dynamics: Audit cuts, transition pacing, and asset placements to make sure there are no dead frames, abrupt clip cuts, or lagging structural pauses.
"""

st.set_page_config(page_title="Zirateh QC Engine", layout="wide")

# Sidebar setup for corporate configuration
st.sidebar.title("🔐 Corporate Configuration")
api_key = st.sidebar.text_input("Enter Corporate API Key (AQ...)", type="password")
project_id = st.sidebar.text_input("GCP Project ID", value="386763638351")
location = st.sidebar.text_input("GCP Vertex Region", value="us-central1")

st.title("🎬 Zirateh AI Video QC Engine")
st.write("Upload your video asset and project brief to run an automated corporate compliance audit.")

if not api_key:
    st.info("Please enter your Vertex API Key in the left sidebar to unlock the application.", icon="🔑")
else:
    # Set the environment variable required for the new corporate SDK routing backend
    os.environ["GEMINI_API_KEY"] = api_key
    
    # Initialize the modern corporate client routing to Vertex infrastructure natively
    client = genai.Client(
        vertex=True,
        project=project_id,
        location=location
    )
    
    # Create two columns for clean layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 1. Project Brief Input")
        brief_type = st.radio("Choose brief format:", ["Upload Master File (Image/PDF)", "Type/Paste Text"])
        
        brief_part = None
        brief_text_content = ""
        target_section = ""
        
        if brief_type == "Upload Master File (Image/PDF)":
            uploaded_brief = st.file_uploader("Upload your master brief document or table image", type=["png", "jpg", "jpeg", "pdf"])
            if uploaded_brief:
                brief_part = types.Part.from_bytes(
                    data=uploaded_brief.getvalue(),
                    mime_type=uploaded_brief.type,
                )
                st.success("📁 Master brief file attached.")
            
            target_section = st.text_input(
                "Target Content Number / Item ID:", 
                placeholder="e.g., Content #3, Project 14, or Number 1"
            )
            if target_section:
                st.info(f"🎯 AI Filter Activated: Gemini will search specifically for section '{target_section}' inside your uploaded document.")
        else:
            brief_text_content = st.text_area("Paste text brief details here:", height=150)

        st.subheader("🎥 2. Video Asset")
        uploaded_video = st.file_uploader("Upload the video file to audit (.mp4, .mov)", type=["mp4", "mov", "avi", "mkv"])
        if uploaded_video:
            st.video(uploaded_video)

    with col2:
        st.subheader("⚙️ 3. Audit Controls")
        st.markdown("**🔒 Active QC Checklist Matrix:** *Standard corporate matrix pre-loaded successfully.*")
        
        with st.expander("View Active Standard Parameters"):
            st.text(STANDARD_QC_CHECKLIST)

        if st.button("🚀 Run AI Compliance Audit", use_container_width=True):
            if not uploaded_video:
                st.error("Please upload a video file before running the audit.")
            elif brief_type == "Upload Master File (Image/PDF)" and not brief_part:
                st.error("Please upload your master brief file.")
            elif brief_type == "Type/Paste Text" and not brief_text_content.strip():
                st.error("Please enter text details for your project brief.")
            else:
                with st.spinner("Processing video and documents with Corporate Vertex AI... This can take 1-2 minutes."):
                    try:
                        # Save uploaded file to local disk temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_video.name)[1]) as tfile:
                            tfile.write(uploaded_video.read())
                            video_path = tfile.name

                        st.text("Uploading video track to corporate Vertex buckets...")
                        uploaded_file_ref = client.files.upload(file=video_path)
                        
                        # Wait out processing queue safely
                        while uploaded_file_ref.state.name == "PROCESSING":
                            time.sleep(5)
                            uploaded_file_ref = client.files.get(name=uploaded_file_ref.name)

                        if uploaded_file_ref.state.name == "FAILED":
                            raise Exception("Video processing failed on corporate servers.")

                        st.text("Analyzing video track against targeted rules...")
                        
                        filter_instruction = f"Locate the specific section marked as '{target_section}' within the attached master file document/image. Extract its layout constraints, text, branding guidelines, or pricing rules, and ignore all other numbers/projects in the file." if target_section else "Extract layout constraints, pricing, and timing details from the document."

                        prompt = f"""
                        You are an expert Executive Video Producer and Senior Quality Control Inspector.
                        Analyze this video against the following two control foundations:
                        
                        FOUNDATION 1: FIXED QC MATRIX PARAMETERS:
                        {STANDARD_QC_CHECKLIST}
                        
                        FOUNDATION 2: PROJECT BRIEF SPECIFICATIONS:
                        {brief_text_content if brief_text_content else filter_instruction}
                        
                        Provide your audit assessment in a clean, strict JSON format with this structure:
                        {{
                            "status": "PASSED" or "REVISIONS REQUIRED",
                            "summary": "Overall execution overview paragraph...",
                            "checklist_results": [
                                {{"parameter": "Technical QC", "result": "PASS/FAIL", "notes": "Specific detail..."}},
                                {{"parameter": "Structure", "result": "PASS/FAIL", "notes": "Specific detail..."}},
                                {{"parameter": "Copy & Text", "result": "PASS/FAIL", "notes": "Specific detail..."}},
                                {{"parameter": "Compliance", "result": "PASS/FAIL", "notes": "
