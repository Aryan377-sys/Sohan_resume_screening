# database.py
import sqlite3
import json
import logging
from models import ResumeInfo, JobDescriptionInfo # To help with type hinting if needed

logger = logging.getLogger(__name__)
DB_NAME = "candidates_data.db"

def setup_database():
    """Creates the SQLite database and the necessary tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Create a table to store candidate application details
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            candidate_email TEXT,
            applied_job_title TEXT,
            match_score REAL,
            feedback TEXT,
            resume_data TEXT, -- Storing full resume JSON
            jd_data TEXT,     -- Storing full JD JSON used for matching
            application_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        # You could create separate normalized tables for skills, experience etc.
        # for more complex querying, but storing JSON blobs is simpler for this example.

        conn.commit()
        logger.info(f"Database '{DB_NAME}' setup complete.")
    except sqlite3.Error as e:
        logger.error(f"Database error during setup: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

def save_match_results(
    resume_info: ResumeInfo,
    jd_info: JobDescriptionInfo,
    match_score: float,
    feedback: str
):
    """Saves the parsed resume, JD, match score, and feedback to the database."""
    conn = None # Ensure conn is defined for the finally block
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        resume_json = resume_info.json()
        jd_json = jd_info.json()

        cursor.execute("""
        INSERT INTO applications (
            candidate_name, candidate_email, applied_job_title,
            match_score, feedback, resume_data, jd_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            resume_info.candidate_name,
            resume_info.email,
            jd_info.job_title,
            match_score,
            feedback,
            resume_json,
            jd_json
        ))

        conn.commit()
        logger.info(f"Saved match result for {resume_info.candidate_name} applying for {jd_info.job_title}.")
        return True # Indicate success

    except sqlite3.Error as e:
        logger.error(f"Database error saving match results: {e}", exc_info=True)
        return False # Indicate failure
    finally:
        if conn:
            conn.close()

# --- Optional: Function to query data (e.g., for a more advanced dashboard) ---
# def get_applications_for_job(job_title: str):
#     conn = None
#     try:
#         conn = sqlite3.connect(DB_NAME)
#         conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM applications WHERE applied_job_title = ? ORDER BY match_score DESC", (job_title,))
#         results = cursor.fetchall()
#         return [dict(row) for row in results] # Convert to list of dicts
#     except sqlite3.Error as e:
#         logger.error(f"Database error fetching applications for {job_title}: {e}", exc_info=True)
#         return []
#     finally:
#         if conn:
#             conn.close()

# Initialize DB on first import (or call explicitly in main)
# setup_database() # Call this once when your application starts