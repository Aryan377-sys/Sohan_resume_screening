# resume_parser.py
import io
from pypdf import PdfReader
from docx import Document as DocxDocument
from models import ResumeInfo
import json
import logging
import os
import requests # Import requests
from dotenv import load_dotenv

load_dotenv() # Load .env file

# --- DeepSeek API Configuration ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions" # Verify the correct endpoint
DEEPSEEK_MODEL = "deepseek-chat" # Verify the best model for this task
# --- End Configuration ---

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_deepseek_for_resume_parsing(text: str) -> str:
    """Calls the DeepSeek API to parse resume text into ResumeInfo JSON."""
    logger.info("Calling DeepSeek API for resume parsing...")
    if not DEEPSEEK_API_KEY:
        logger.error("DeepSeek API Key not found in environment variables.")
        return json.dumps({}) # Return empty JSON string on error

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    # Construct the prompt - instruct it to return JSON based on ResumeInfo schema
    prompt = f"""
    Parse the following resume text and extract the information strictly according to the provided JSON schema.
    Ensure the output is ONLY a valid JSON object matching the schema, without any extra text or markdown formatting like ```json.
    Schema: {ResumeInfo.schema_json(indent=2)}
    Resume Text:
    ---
    {text}
    ---
    Valid JSON Output:
    """

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}, # Request JSON output
        "temperature": 0.1, # Lower temperature for more deterministic parsing
        # "max_tokens": 2048, # Adjust if needed, depends on resume length and model limits
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=90) # Increased timeout for potentially long resumes
        response.raise_for_status()
        response_data = response.json()

        if 'choices' in response_data and len(response_data['choices']) > 0:
            message_content = response_data['choices'][0].get('message', {}).get('content', '{}')
            # Validate if it's proper JSON before returning
            try:
                json.loads(message_content)
                logger.info("DeepSeek API call successful for resume parsing.")
                return message_content
            except json.JSONDecodeError:
                logger.error(f"DeepSeek API returned invalid JSON for resume parsing: {message_content[:500]}...") # Log first 500 chars
                # Attempt to extract JSON if wrapped in markdown
                if "```json" in message_content:
                    try:
                        extracted_json = message_content.split("```json")[1].split("```")[0].strip()
                        json.loads(extracted_json)
                        logger.info("Successfully extracted JSON wrapped in markdown.")
                        return extracted_json
                    except Exception as json_extract_error:
                        logger.error(f"Failed to extract JSON from markdown: {json_extract_error}")
                return json.dumps({}) # Return empty if invalid or extraction failed
        else:
            logger.error(f"Unexpected response structure from DeepSeek API (resume parsing): {response_data}")
            return json.dumps({})

    except requests.exceptions.Timeout:
        logger.error("DeepSeek API request timed out during resume parsing.")
        return json.dumps({})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling DeepSeek API for resume parsing: {e}", exc_info=True)
        return json.dumps({})
    except Exception as e:
        logger.error(f"An unexpected error occurred during DeepSeek resume parsing call: {e}", exc_info=True)
        return json.dumps({})


def parse_resume_file(uploaded_file: io.BytesIO, filename: str) -> ResumeInfo:
    """Parses the uploaded resume file (PDF or DOCX) into structured JSON using DeepSeek."""
    text = ""
    try:
        # Reset stream position just in case
        uploaded_file.seek(0)
        if filename.lower().endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        elif filename.lower().endswith('.docx'):
            doc = DocxDocument(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif filename.lower().endswith('.txt'):
             uploaded_file.seek(0)
             text = uploaded_file.read().decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file type: {filename}. Please upload PDF, DOCX, or TXT.")

        if not text or text.isspace():
            logger.warning(f"Could not extract text or text is empty/whitespace from {filename}")
            raise ValueError("Could not extract text from file or file is empty.")

        logger.info(f"Extracted text from {filename}. Length: {len(text)}. Calling LLM...")

        # Call DeepSeek LLM to parse the extracted text
        json_output_str = call_deepseek_for_resume_parsing(text)

        if not json_output_str or json_output_str == '{}':
             logger.error("Received empty or invalid JSON from DeepSeek resume parsing.")
             raise ValueError("LLM failed to parse resume, returned empty data.")

        # Parse the LLM JSON output using the Pydantic model
        parsed_data = json.loads(json_output_str)
        resume_info = ResumeInfo(**parsed_data)

        # Basic check: ensure at least some core info was parsed
        if not resume_info.candidate_name and not resume_info.email and not resume_info.skills:
             logger.warning(f"Resume parsing resulted in mostly empty fields for {filename}.")
             # Decide if this is an error or just a poor parse
             # raise ValueError("Parsed resume data is missing critical information.") # Option to make it stricter

        logger.info(f"Successfully parsed resume via DeepSeek for: {resume_info.candidate_name or filename}")
        return resume_info

    except Exception as e:
        logger.error(f"Error parsing resume file {filename}: {e}", exc_info=True)
        # Re-raise as a runtime error to be caught by the LangGraph node
        raise RuntimeError(f"Failed to parse resume '{filename}': {e}") from e