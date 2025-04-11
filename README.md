# AI Resume Matcher 📄

## Overview

This project is an AI-powered application designed to automate the initial screening process of job applicants. It takes an uploaded resume (CV) and compares it against a selected job description from a predefined list. Using the DeepSeek Large Language Model (LLM) API, it parses both documents, calculates a match score percentage, generates feedback for the candidate, and sends automated emails based on qualification criteria. The results are displayed on a simple web dashboard built with Streamlit.

The workflow is orchestrated using LangGraph, allowing for a clear, stateful execution of different processing steps (agents).

## Features

* **Resume Upload:** Supports uploading resumes in PDF (.pdf), Word (.docx), and Text (.txt) formats.
* **Job Selection:** Allows selecting a specific job role from a list defined in a CSV file.
* **AI-Powered Parsing:** Uses the DeepSeek API to parse unstructured text from resumes and job descriptions into structured JSON data based on predefined models.
* **AI Matching & Feedback:** Employs the DeepSeek API to compare the parsed resume against the job description requirements, calculate a percentage match score, and generate constructive feedback for the candidate.
* **Automated Email Notifications:** Sends congratulatory emails (if match score >= 65%) or rejection emails (if score < 65%) to the candidate, including the generated feedback.
* **Data Storage:** Saves application details (parsed data, score, feedback) into an SQLite database for record-keeping.
* **Streamlit Dashboard:** Provides a simple web interface for uploading resumes, selecting jobs, triggering the process, and viewing the results (score, feedback, processing status).

## How it Works (Workflow)

The application follows a defined sequence orchestrated by LangGraph:

1.  **User Interaction (Streamlit UI - `main.py`):**
    * The user accesses the web application built with Streamlit.
    * They select a Job Title from a dropdown list (populated from `jobs.csv`).
    * They upload a candidate's resume file.
    * They click the "Match Resume to Job Description" button.

2.  **Workflow Initialization (LangGraph - `main.py`):**
    * The Streamlit app prepares the initial data (uploaded file content, selected job title).
    * It invokes the LangGraph workflow.

3.  **Input Loading & Validation (Node: `load_validate` - `main.py`):**
    * Loads the job descriptions from `jobs.csv`.
    * Validates that the necessary inputs (resume, job title) are present.

4.  **Agent 1: Resume Parsing (Node: `parse_resume` - `resume_parser.py`):**
    * Extracts text content from the uploaded resume file (PDF, DOCX, TXT).
    * Calls the DeepSeek API (`call_deepseek_for_resume_parsing`) with a specific prompt to analyze the text and structure it into a predefined JSON format (`ResumeInfo` model from `models.py`).
    * Updates the workflow state with the parsed resume data.

5.  **Agent 2: Job Description Parsing (Node: `parse_jd` - `jd_parser.py`):**
    * Finds the selected job title in the loaded `jobs.csv` data.
    * Retrieves the corresponding job description text.
    * Calls the DeepSeek API (`call_deepseek_for_jd_parsing`) with a specific prompt to analyze the text and structure it into a predefined JSON format (`JobDescriptionInfo` model from `models.py`).
    * Updates the workflow state with the parsed job description data.

6.  **Agent 3: Matching & Feedback (Node: `match` - `matcher.py`):**
    * Takes the structured resume and job description data (as JSON).
    * Calls the DeepSeek API (`call_deepseek_for_matching`) with a specific prompt asking it to:
        * Compare the resume against the job requirements.
        * Calculate a match score (0-100).
        * Generate constructive feedback text.
    * Updates the workflow state with the score and feedback.

7.  **Data Storage (Node: `save_db` - `database.py`):**
    * Connects to the SQLite database (`candidates_data.db`).
    * Saves the candidate details, applied job, parsed data (JSON), match score, and feedback into the `applications` table.

8.  **Email Notification (Node: `send_email` - `email_sender.py`):**
    * Checks the candidate's email address (parsed from the resume).
    * Checks the match score.
    * Constructs either a congratulatory email (score >= 65) or a rejection email (score < 65), including the generated feedback.
    * Uses SMTP credentials from the `.env` file to send the email.

9.  **Display Results (Streamlit UI - `main.py`):**
    * Once the LangGraph workflow completes, the final state is returned to Streamlit.
    * The UI updates to display the match score, feedback, database save status, and email sent status.
    * An expander allows viewing the raw parsed JSON data for debugging/details.

*Error Handling:* If any step fails (e.g., API error, file parsing error), the error is caught, logged, stored in the workflow state, and displayed in the Streamlit UI, often causing subsequent steps to be skipped.

## Project Structure

Okay, here is a comprehensive README file suitable for GitHub, explaining the project structure and workflow in a way that should be understandable even for beginners.

Markdown

# AI Resume Matcher 📄🤖

## Overview

This project is an AI-powered application designed to automate the initial screening process of job applicants. It takes an uploaded resume (CV) and compares it against a selected job description from a predefined list. Using the DeepSeek Large Language Model (LLM) API, it parses both documents, calculates a match score percentage, generates feedback for the candidate, and sends automated emails based on qualification criteria. The results are displayed on a simple web dashboard built with Streamlit.

The workflow is orchestrated using LangGraph, allowing for a clear, stateful execution of different processing steps (agents).

## Features

* **Resume Upload:** Supports uploading resumes in PDF (.pdf), Word (.docx), and Text (.txt) formats.
* **Job Selection:** Allows selecting a specific job role from a list defined in a CSV file.
* **AI-Powered Parsing:** Uses the DeepSeek API to parse unstructured text from resumes and job descriptions into structured JSON data based on predefined models.
* **AI Matching & Feedback:** Employs the DeepSeek API to compare the parsed resume against the job description requirements, calculate a percentage match score, and generate constructive feedback for the candidate.
* **Automated Email Notifications:** Sends congratulatory emails (if match score >= 65%) or rejection emails (if score < 65%) to the candidate, including the generated feedback.
* **Data Storage:** Saves application details (parsed data, score, feedback) into an SQLite database for record-keeping.
* **Streamlit Dashboard:** Provides a simple web interface for uploading resumes, selecting jobs, triggering the process, and viewing the results (score, feedback, processing status).

## How it Works (Workflow)

The application follows a defined sequence orchestrated by LangGraph:

1.  **User Interaction (Streamlit UI - `main.py`):**
    * The user accesses the web application built with Streamlit.
    * They select a Job Title from a dropdown list (populated from `jobs.csv`).
    * They upload a candidate's resume file.
    * They click the "Match Resume to Job Description" button.

2.  **Workflow Initialization (LangGraph - `main.py`):**
    * The Streamlit app prepares the initial data (uploaded file content, selected job title).
    * It invokes the LangGraph workflow.

3.  **Input Loading & Validation (Node: `load_validate` - `main.py`):**
    * Loads the job descriptions from `jobs.csv`.
    * Validates that the necessary inputs (resume, job title) are present.

4.  **Agent 1: Resume Parsing (Node: `parse_resume` - `resume_parser.py`):**
    * Extracts text content from the uploaded resume file (PDF, DOCX, TXT).
    * Calls the DeepSeek API (`call_deepseek_for_resume_parsing`) with a specific prompt to analyze the text and structure it into a predefined JSON format (`ResumeInfo` model from `models.py`).
    * Updates the workflow state with the parsed resume data.

5.  **Agent 2: Job Description Parsing (Node: `parse_jd` - `jd_parser.py`):**
    * Finds the selected job title in the loaded `jobs.csv` data.
    * Retrieves the corresponding job description text.
    * Calls the DeepSeek API (`call_deepseek_for_jd_parsing`) with a specific prompt to analyze the text and structure it into a predefined JSON format (`JobDescriptionInfo` model from `models.py`).
    * Updates the workflow state with the parsed job description data.

6.  **Agent 3: Matching & Feedback (Node: `match` - `matcher.py`):**
    * Takes the structured resume and job description data (as JSON).
    * Calls the DeepSeek API (`call_deepseek_for_matching`) with a specific prompt asking it to:
        * Compare the resume against the job requirements.
        * Calculate a match score (0-100).
        * Generate constructive feedback text.
    * Updates the workflow state with the score and feedback.

7.  **Data Storage (Node: `save_db` - `database.py`):**
    * Connects to the SQLite database (`candidates_data.db`).
    * Saves the candidate details, applied job, parsed data (JSON), match score, and feedback into the `applications` table.

8.  **Email Notification (Node: `send_email` - `email_sender.py`):**
    * Checks the candidate's email address (parsed from the resume).
    * Checks the match score.
    * Constructs either a congratulatory email (score >= 65) or a rejection email (score < 65), including the generated feedback.
    * Uses SMTP credentials from the `.env` file to send the email.

9.  **Display Results (Streamlit UI - `main.py`):**
    * Once the LangGraph workflow completes, the final state is returned to Streamlit.
    * The UI updates to display the match score, feedback, database save status, and email sent status.
    * An expander allows viewing the raw parsed JSON data for debugging/details.

*Error Handling:* If any step fails (e.g., API error, file parsing error), the error is caught, logged, stored in the workflow state, and displayed in the Streamlit UI, often causing subsequent steps to be skipped.

## Project Structure

resume-matcher/
├── .env               # Stores API keys, email credentials (!! ADD TO .gitignore !!)
├── .gitignore         # Specifies files/folders to ignore for Git (e.g., .env, *.db)
├─ venv                 # Virtual environment
├── requirements.txt   # Lists Python dependencies needed for the project
├── jobs.csv           # CSV file containing predefined job descriptions
├── main.py            # Main Streamlit application script & LangGraph orchestrator
├── resume_parser.py   # Agent 1: Logic for parsing uploaded resumes using DeepSeek API
├── jd_parser.py       # Agent 2: Logic for parsing job descriptions from CSV using DeepSeek API
├── matcher.py         # Agent 3: Logic for matching resume to JD and generating feedback using DeepSeek API
├── models.py          # Defines Pydantic data models (schemas) for structured resume and JD info
├── database.py        # Handles SQLite database setup and data saving operations
├── email_sender.py    # Utility functions for sending emails via SMTP
└── candidates_data.db # SQLite database file (created automatically on first run)

**File Explanations:**

* **`main.py`**: The entry point of the application. It sets up the Streamlit user interface, defines the LangGraph state and nodes, builds the workflow graph, and handles the execution flow when the user interacts with the UI.
* **`models.py`**: Contains Pydantic models (`ResumeInfo`, `JobDescriptionInfo`, etc.). These define the expected structure (schema) for the data extracted from resumes and job descriptions, ensuring consistency.
* **`resume_parser.py`**: Focuses solely on processing the uploaded resume file. It reads the file content, extracts text, calls the DeepSeek API for parsing based on the `ResumeInfo` model, and returns the structured data. Acts as "Agent 1".
* **`jd_parser.py`**: Handles fetching the correct job description text from the `jobs.csv` based on user selection, calls the DeepSeek API for parsing based on the `JobDescriptionInfo` model, and returns the structured data. Acts as "Agent 2".
* **`matcher.py`**: Performs the core comparison logic. It takes the structured resume and JD data, calls the DeepSeek API to get a match score and feedback, and returns these results. Acts as "Agent 3".
* **`database.py`**: Manages all interactions with the SQLite database. Includes functions to set up the database tables (`setup_database`) and save the results of an application analysis (`save_match_results`).
* **`email_sender.py`**: Contains the function (`send_application_email`) responsible for constructing and sending emails using the credentials provided in the `.env` file.
* **`jobs.csv`**: A simple Comma Separated Values file where you define the available jobs. Must contain at least `Job Title` and `Job Description` columns. Can optionally include `Company` and `Location`.
* **`.env`**: A crucial configuration file (!!! **DO NOT COMMIT TO GIT** !!!). Stores sensitive information like your DeepSeek API key and email sending credentials (username/password or app password).
* **`requirements.txt`**: Lists all the external Python libraries the project depends on (e.g., `streamlit`, `langgraph`, `requests`, `pypdf`). Allows easy installation using `pip`.
* **`.gitignore`**: Tells Git which files or directories to ignore (e.g., `.env` file, the `*.db` database file, Python cache files). Essential for security and keeping the repository clean.
* **`candidates_data.db`**: The actual SQLite database file. It gets created automatically by `database.py` when you run the application for the first time if it doesn't exist.

## Setup and Installation

Follow these steps to set up and run the project locally:

1.  **Prerequisites:**
    * Python 3.8 or higher installed.
    * `pip` (Python package installer) available.
    * Git installed (for cloning).

2.  **Clone the Repository:**
    ```bash
    git clone <https://github.com/Aryan377-sys/Sohan_resume_screening.git> 
    cd resume-matcher
    ```

3.  **Create and Activate Virtual Environment (Recommended):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up Environment Variables (`.env` file):**
    * Make a copy of `.env.example` (if provided) or create a new file named `.env` in the project's root directory (`resume-matcher/`).
    * Edit the `.env` file and add your actual credentials:
        ```dotenv
        DEEPSEEK_API_KEY="sk-YOUR_DEEPSEEK_API_KEY"
        SMTP_SERVER="smtp.example.com" # e.g., smtp.gmail.com
        SMTP_PORT=587 # Or your provider's port (e.g., 465 for SSL)
        EMAIL_SENDER="your_email@example.com"
        EMAIL_PASSWORD="your_email_password_or_app_password"
        ```
    * **IMPORTANT:** Ensure the `.env` file is listed in your `.gitignore` file to prevent accidentally committing sensitive keys.

6.  **Prepare `jobs.csv`:**
    * Make sure the `jobs.csv` file exists in the root directory.
    * It **must** contain columns named `Job Title` and `Job Description`.
    * You can optionally add `Company` and `Location` columns.
    * Populate it with the job roles you want to screen for. *Example:*
        ```csv
        Job Title,Job Description,Company,Location
        Software Engineer,"Develop backend services using Python/Django...",Tech Solutions Inc.,Remote
        Data Analyst,"Analyze data, create reports using SQL/Python...",Data Insights Co.,New York
        ```

7.  **Database Initialization:**
    * The SQLite database (`candidates_data.db`) and its table (`applications`) will be created automatically by `database.py` the first time you run `main.py` if the file doesn't already exist.

## Running the Application

1.  Make sure your virtual environment is activated.
2.  Navigate to the project's root directory (`resume-matcher/`) in your terminal.
3.  Run the Streamlit application:
    ```bash
    streamlit run main.py
    ```
4.  Streamlit will provide a local URL (usually `http://localhost:8501`). Open this URL in your web browser.
5.  Use the web interface to select a job, upload a resume, and start the matching process.

## Configuration

* **API Key:** The `DEEPSEEK_API_KEY` in the `.env` file is essential for the AI features to work.
* **Email:** Configure `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_SENDER`, and `EMAIL_PASSWORD` in `.env` for email notifications. Note that for Gmail, you might need to enable "Less secure app access" (not recommended) or preferably generate an "App Password" if you use 2-Factor Authentication.
* **Job Data:** Modify `jobs.csv` to reflect the actual job roles you are hiring for.
* **DeepSeek Model:** You can change the `DEEPSEEK_MODEL` variable inside `resume_parser.py`, `jd_parser.py`, and `matcher.py` if you want to experiment with different DeepSeek models (check their documentation for available models suitable for chat/completion and JSON output).
* **Match Threshold:** The 65% threshold for sending congratulatory vs. rejection emails is currently hardcoded in `email_sender.py`. You can adjust this value if needed.

## Technology Stack

* **Backend:** Python 3
* **Web Framework/UI:** Streamlit
* **Workflow Orchestration:** LangGraph
* **AI Model:** DeepSeek API (via `requests`)
* **File Parsing:** PyPDF2 (for PDFs), python-docx (for DOCX)
* **Data Handling:** Pandas (for CSV), Pydantic (for data validation/modeling)
* **Database:** SQLite3
* **Environment Variables:** python-dotenv

## Important Notes & Caveats

* **API Costs:** Calling the DeepSeek API incurs costs based on usage (input/output tokens). Be mindful of this when processing many documents.
* **Security:** **Never** commit your `.env` file containing API keys or passwords to Git or share it publicly. Use the `.gitignore` file properly.
* **Email Content:** The email templates in `email_sender.py` are basic examples. Customize them to match your company's tone and provide more specific next steps or information.
* **Error Handling:** While basic error handling is included, complex edge cases or API downtime might require more robust error management. API calls include timeouts, but network issues can still occur.
* **Parsing Accuracy:** LLM parsing is powerful but not perfect. The accuracy of extracted information depends on the resume/JD format, the LLM's capabilities, and the quality of the prompts used. Some manual review might still be necessary.
* **No Model Training:** This application *uses* a pre-trained LLM API; it does *not* train or fine-tune any models on your data. The database stores application records, not training data.
* **DeepSeek Client:** This implementation uses the standard `requests` library. If DeepSeek provides an official Python client library, consider switching to that for potentially easier usage or added features.


