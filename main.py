# main.py
import streamlit as st
import pandas as pd
from typing import TypedDict, Optional, Dict, Any
import io
import os
import logging

# Import functions from other modules
from resume_parser import parse_resume_file
from jd_parser import parse_job_description
from matcher import calculate_match_and_feedback
from database import setup_database, save_match_results
from email_sender import send_application_email
from models import ResumeInfo, JobDescriptionInfo

# LangGraph imports
from langgraph.graph import StateGraph, END

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
JOB_DATA_CSV = "/home/sohanx1/Downloads/Sohan/Accenture/Dataset/[Usecase 5] AI-Powered Job Application Screening System​/job_description.csv"
DATABASE_NAME = "candidates_data.db"

# --- LangGraph State Definition ---
class AppState(TypedDict):
    """Defines the state that flows through the graph."""
    uploaded_file_content: Optional[bytes]
    uploaded_filename: Optional[str]
    selected_job_title: Optional[str]
    job_descriptions_df: Optional[pd.DataFrame]
    parsed_resume: Optional[ResumeInfo]
    parsed_jd: Optional[JobDescriptionInfo]
    match_score: Optional[float]
    feedback: Optional[str]
    db_save_status: bool
    email_sent_status: bool
    error_message: Optional[str] # To capture errors during processing

# --- LangGraph Node Functions ---

def load_and_validate_input(state: AppState) -> AppState:
    """Loads job descriptions and validates initial inputs."""
    logger.info("Node: load_and_validate_input")
    try:
        if not os.path.exists(JOB_DATA_CSV):
            raise FileNotFoundError(f"Job descriptions file not found: {JOB_DATA_CSV}")
        df = pd.read_csv(JOB_DATA_CSV,encoding='latin-1')
        # Basic validation (check if required columns exist)
        if 'Job Title' not in df.columns or 'Job Description' not in df.columns:
             raise ValueError("CSV must contain 'Job Title' and 'Job Description' columns.")
        state['job_descriptions_df'] = df

        # Check other inputs from Streamlit (already set before invoking graph)
        if not state.get('uploaded_file_content') or not state.get('uploaded_filename'):
            raise ValueError("Resume file not provided.")
        if not state.get('selected_job_title'):
            raise ValueError("Job title not selected.")

        state['error_message'] = None # Clear previous errors
        logger.info("Initial input validation successful.")
        return state
    except Exception as e:
        logger.error(f"Error in load_and_validate_input: {e}", exc_info=True)
        state['error_message'] = f"Initialization Error: {e}"
        return state # Propagate error state

def process_resume(state: AppState) -> AppState:
    """Node to parse the uploaded resume."""
    logger.info("Node: process_resume")
    if state.get('error_message'): return state # Skip if error occurred previously

    try:
        file_content = state['uploaded_file_content']
        filename = state['uploaded_filename']
        file_like_object = io.BytesIO(file_content) # Create file-like object
        parsed_resume = parse_resume_file(file_like_object, filename)
        state['parsed_resume'] = parsed_resume
        state['error_message'] = None
        logger.info(f"Resume parsed successfully for candidate: {parsed_resume.candidate_name}")
        return state
    except Exception as e:
        logger.error(f"Error in process_resume: {e}", exc_info=True)
        state['error_message'] = f"Resume Parsing Failed: {e}"
        state['parsed_resume'] = None
        return state

def process_job_description(state: AppState) -> AppState:
    """Node to parse the selected job description."""
    logger.info("Node: process_job_description")
    if state.get('error_message'): return state

    try:
        job_title = state['selected_job_title']
        df = state['job_descriptions_df']
        parsed_jd = parse_job_description(job_title, df)
        state['parsed_jd'] = parsed_jd
        state['error_message'] = None
        logger.info(f"Job description parsed successfully for: {parsed_jd.job_title}")
        return state
    except Exception as e:
        logger.error(f"Error in process_job_description: {e}", exc_info=True)
        state['error_message'] = f"Job Description Parsing Failed: {e}"
        state['parsed_jd'] = None
        return state

def perform_matching(state: AppState) -> AppState:
    """Node to compare resume and JD, calculate score, and generate feedback."""
    logger.info("Node: perform_matching")
    if state.get('error_message') or not state.get('parsed_resume') or not state.get('parsed_jd'):
        if not state.get('error_message'): # Add error if inputs are missing but no error recorded yet
            state['error_message'] = "Cannot perform matching due to missing parsed resume or JD."
        return state

    try:
        resume = state['parsed_resume']
        jd = state['parsed_jd']
        score, feedback_text = calculate_match_and_feedback(resume, jd)
        state['match_score'] = score
        state['feedback'] = feedback_text
        state['error_message'] = None
        logger.info(f"Matching complete. Score: {score}")
        return state
    except Exception as e:
        logger.error(f"Error in perform_matching: {e}", exc_info=True)
        state['error_message'] = f"Matching Failed: {e}"
        state['match_score'] = None
        state['feedback'] = None
        return state

def save_to_database(state: AppState) -> AppState:
    """Node to save the results to the SQLite database."""
    logger.info("Node: save_to_database")
    # Proceed even if there was a matching error, to potentially save partial data or error state?
    # Or only save on success? Let's only save if matching was successful.
    if state.get('error_message') or state.get('match_score') is None:
        logger.warning("Skipping database save due to previous error or missing match score.")
        state['db_save_status'] = False
        # Optionally add specific db error message if needed
        # state['error_message'] = state.get('error_message') or "Database save skipped."
        return state

    try:
        success = save_match_results(
            resume_info=state['parsed_resume'],
            jd_info=state['parsed_jd'],
            match_score=state['match_score'],
            feedback=state['feedback']
        )
        state['db_save_status'] = success
        if not success:
            # If save_match_results returned False, log it but don't overwrite existing graph error
            logger.error("Database save operation returned False.")
            if not state.get('error_message'): # Add error if none exists yet
                 state['error_message'] = "Failed to save results to the database."
        else:
             logger.info("Results saved to database successfully.")
             state['error_message'] = None # Clear any previous non-fatal error? Maybe not.
        return state
    except Exception as e:
        logger.error(f"Error in save_to_database node: {e}", exc_info=True)
        state['error_message'] = f"Database Save Failed: {e}"
        state['db_save_status'] = False
        return state

def send_candidate_email(state: AppState) -> AppState:
    """Node to send the email to the candidate."""
    logger.info("Node: send_candidate_email")
    # Should we send email if DB save failed? Maybe. Depends on requirements.
    # Let's proceed if matching was done, regardless of DB status for now.
    if state.get('match_score') is None or not state.get('parsed_resume') or not state.get('feedback'):
         logger.warning("Skipping email sending due to missing score, resume info, or feedback.")
         state['email_sent_status'] = False
         if not state.get('error_message'):
             state['error_message'] = "Email not sent due to missing information."
         return state

    try:
        resume_info = state['parsed_resume']
        success = send_application_email(
            to_email=resume_info.email,
            candidate_name=resume_info.candidate_name,
            job_title=state['selected_job_title'], # Use selected title
            match_score=state['match_score'],
            feedback=state['feedback']
        )
        state['email_sent_status'] = success
        if not success and not state.get('error_message'): # Add error if sending failed and no prior error exists
             state['error_message'] = "Failed to send email (check logs and email config)."

        logger.info(f"Email sending status: {success}")
        # Don't clear error message here, as email sending failure is important
        return state
    except Exception as e:
        logger.error(f"Error in send_candidate_email node: {e}", exc_info=True)
        state['error_message'] = f"Email Sending Failed: {e}"
        state['email_sent_status'] = False
        return state

# --- Graph Definition ---
def build_graph():
    workflow = StateGraph(AppState)

    # Add nodes
    workflow.add_node("load_validate", load_and_validate_input)
    workflow.add_node("parse_resume", process_resume)
    workflow.add_node("parse_jd", process_job_description)
    workflow.add_node("match", perform_matching)
    workflow.add_node("save_db", save_to_database)
    workflow.add_node("send_email", send_candidate_email)

    # Define edges
    workflow.set_entry_point("load_validate")

    # Conditional routing based on errors
    workflow.add_conditional_edges(
        "load_validate",
        lambda state: "parse_resume" if not state.get("error_message") else END,
        {"parse_resume": "parse_resume", END: END}
    )
    workflow.add_conditional_edges(
        "parse_resume",
        lambda state: "parse_jd" if not state.get("error_message") else END,
        {"parse_jd": "parse_jd", END: END}
    )
    workflow.add_conditional_edges(
        "parse_jd",
        lambda state: "match" if not state.get("error_message") else END,
        {"match": "match", END: END}
    )
    workflow.add_conditional_edges(
        "match",
        # Proceed to save even if matching had issues? No, let's stop on matching error.
        lambda state: "save_db" if not state.get("error_message") else END,
        {"save_db": "save_db", END: END}
    )
    # Decide whether DB save failure should stop email sending. Let's allow email even if DB fails.
    # So, save_db always goes to send_email, but send_email might skip if data is missing.
    workflow.add_edge("save_db", "send_email")

    # Final edge
    workflow.add_edge("send_email", END)


    # Compile the graph
    app_graph = workflow.compile()
    logger.info("LangGraph compiled successfully.")
    return app_graph

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("📄🤖 AI Resume Matcher")

# Initialize Database
try:
    setup_database()
    logger.info("Database setup checked/initialized.")
except Exception as e:
    st.error(f"Fatal Error: Could not initialize database: {e}")
    st.stop() # Stop the app if DB isn't ready

# Load Job Descriptions for Selectbox
try:
    if not os.path.exists(JOB_DATA_CSV):
         st.error(f"Error: The job descriptions file '{JOB_DATA_CSV}' was not found.")
         st.stop()
    jobs_df = pd.read_csv(JOB_DATA_CSV,encoding='latin-1')
    if 'Job Title' not in jobs_df.columns:
        st.error("Error: CSV file must contain a 'Job Title' column.")
        st.stop()
    job_titles = jobs_df['Job Title'].unique().tolist()
    logger.info(f"Loaded {len(job_titles)} unique job titles from {JOB_DATA_CSV}")
except Exception as e:
    st.error(f"Error loading job descriptions from {JOB_DATA_CSV}: {e}")
    logger.error(f"Failed to load job descriptions: {e}", exc_info=True)
    st.stop()


# --- Input Area ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Select Job")
    selected_job = st.selectbox("Choose the job position:", options=[""] + job_titles) # Add empty option

with col2:
    st.subheader("2. Upload Resume")
    uploaded_resume = st.file_uploader("Upload candidate's resume (PDF or DOCX):", type=['pdf', 'docx', 'txt'])

# --- Processing Area ---
st.subheader("3. Process Application")
process_button = st.button("Match Resume to Job Description")

if process_button:
    if not selected_job:
        st.warning("Please select a job title.")
    elif not uploaded_resume:
        st.warning("Please upload a resume file.")
    else:
        # Compile graph (could be done once outside the button click if preferred)
        try:
            graph = build_graph()
        except Exception as e:
            st.error(f"Failed to build the processing graph: {e}")
            logger.error(f"Graph building failed: {e}", exc_info=True)
            st.stop()


        # Prepare initial state for the graph
        file_bytes = uploaded_resume.getvalue()
        initial_state: AppState = {
            "uploaded_file_content": file_bytes,
            "uploaded_filename": uploaded_resume.name,
            "selected_job_title": selected_job,
            # These will be populated by the graph
            "job_descriptions_df": None,
            "parsed_resume": None,
            "parsed_jd": None,
            "match_score": None,
            "feedback": None,
            "db_save_status": False,
            "email_sent_status": False,
            "error_message": None
        }

        st.info("Processing started... Parsing resume, analyzing job description, and matching.")
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Invoking workflow...")
            # Stream events or just invoke and wait
            # For simplicity, invoke and wait. For long processes, streaming is better.
            final_state = graph.invoke(initial_state)
            progress_bar.progress(100) # Mark as complete
            status_text.text("Processing complete!")
            logger.info("Graph invocation finished.")

            # --- Display Results (Dashboard) ---
            st.subheader("📊 Results & Dashboard")

            if final_state.get("error_message"):
                st.error(f"An error occurred: {final_state['error_message']}")
                logger.error(f"Final state contains error: {final_state['error_message']}")

            # Display Match Score and Feedback regardless of error (if available)
            score = final_state.get('match_score')
            feedback = final_state.get('feedback')
            parsed_resume_info = final_state.get('parsed_resume')
            candidate_name = parsed_resume_info.candidate_name if parsed_resume_info else "Candidate"

            if score is not None:
                 st.metric(label=f"Match Score for {candidate_name}", value=f"{score:.1f}%")
            else:
                 st.warning("Match score could not be calculated.")

            if feedback:
                 st.text_area("Generated Feedback:", value=feedback, height=200, disabled=True)
            else:
                 st.warning("Feedback could not be generated.")

            # Display DB and Email status
            st.markdown("---") # Separator
            col_status1, col_status2 = st.columns(2)
            with col_status1:
                 db_status = final_state.get('db_save_status', False)
                 st.write(f"💾 Database Save Status: {'✅ Success' if db_status else '❌ Failed / Skipped'}")
            with col_status2:
                 email_status = final_state.get('email_sent_status', False)
                 st.write(f"📧 Email Sent Status: {'✅ Success' if email_status else '❌ Failed / Skipped'}")
                 if not email_status and not final_state.get('error_message'):
                     # Check specifically if email creds were the likely issue
                     if not EMAIL_SENDER or not EMAIL_PASSWORD:
                         st.caption("Email sending failed: Check .env configuration for EMAIL_SENDER/PASSWORD.")
                     elif parsed_resume_info and not parsed_resume_info.email:
                          st.caption(f"Email not sent: No email address found in the resume for {candidate_name}.")


            # Optional: Display Parsed Data (for debugging/details)
            with st.expander("View Parsed Data"):
                col_parsed1, col_parsed2 = st.columns(2)
                with col_parsed1:
                    st.write("**Parsed Resume:**")
                    if final_state.get('parsed_resume'):
                        st.json(final_state['parsed_resume'].dict())
                    else:
                        st.write("Resume parsing failed or did not run.")
                with col_parsed2:
                    st.write("**Parsed Job Description:**")
                    if final_state.get('parsed_jd'):
                        st.json(final_state['parsed_jd'].dict())
                    else:
                        st.write("Job description parsing failed or did not run.")

        except Exception as e:
             progress_bar.progress(100) # Ensure progress bar finishes
             status_text.error(f"Workflow execution failed: {e}")
             logger.error(f"Critical error during graph invocation: {e}", exc_info=True)
             st.subheader("📊 Results & Dashboard")
             st.error(f"An unexpected error stopped the process: {e}")

# --- Optional: Add more dashboard features ---
# e.g., A section to query the database and show past applications for the selected job
# st.subheader("Past Applications for this Role")
# if selected_job:
#     past_apps = get_applications_for_job(selected_job) # Assumes you added this function to database.py
#     if past_apps:
#         st.dataframe(pd.DataFrame(past_apps)[['candidate_name', 'match_score', 'application_timestamp']]) # Display subset of columns
#     else:
#         st.write("No past application data found for this job title in the database.")