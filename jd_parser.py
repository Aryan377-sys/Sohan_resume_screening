# jd_parser.py
import pandas as pd
from models import JobDescriptionInfo
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

def call_deepseek_for_jd_parsing(text: str, job_title: str) -> str:
    """Calls the DeepSeek API to parse job description text into JobDescriptionInfo JSON."""
    logger.info(f"Calling DeepSeek API for JD parsing: {job_title}")
    if not DEEPSEEK_API_KEY:
        logger.error("DeepSeek API Key not found in environment variables.")
        return json.dumps({}) # Return empty JSON string

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    # Construct the prompt - instruct it to return JSON based on JobDescriptionInfo schema
    prompt = f"""
    Analyze the following job description for '{job_title}' and extract the key information
    strictly according to the provided JSON schema.
    Ensure the output is ONLY a valid JSON object matching the schema, without any extra text or markdown formatting like ```json.
    Schema: {JobDescriptionInfo.schema_json(indent=2)}
    Job Description Text:
    ---
    {text}
    ---
    Valid JSON Output:
    """

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}, # Request JSON output
        "temperature": 0.1,
        # "max_tokens": 1024, # Adjust if needed
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        response_data = response.json()

        if 'choices' in response_data and len(response_data['choices']) > 0:
            message_content = response_data['choices'][0].get('message', {}).get('content', '{}')
            try:
                json.loads(message_content)
                logger.info("DeepSeek API call successful for JD parsing.")
                return message_content
            except json.JSONDecodeError:
                logger.error(f"DeepSeek API returned invalid JSON for JD parsing: {message_content[:500]}...")
                 # Attempt to extract JSON if wrapped in markdown
                if "```json" in message_content:
                    try:
                        extracted_json = message_content.split("```json")[1].split("```")[0].strip()
                        json.loads(extracted_json)
                        logger.info("Successfully extracted JSON wrapped in markdown (JD).")
                        return extracted_json
                    except Exception as json_extract_error:
                        logger.error(f"Failed to extract JSON from markdown (JD): {json_extract_error}")
                return json.dumps({}) # Return empty if invalid or extraction failed
        else:
            logger.error(f"Unexpected response structure from DeepSeek API (JD parsing): {response_data}")
            return json.dumps({})

    except requests.exceptions.Timeout:
        logger.error("DeepSeek API request timed out during JD parsing.")
        return json.dumps({})
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling DeepSeek API for JD parsing: {e}", exc_info=True)
        return json.dumps({})
    except Exception as e:
        logger.error(f"An unexpected error occurred during DeepSeek JD parsing call: {e}", exc_info=True)
        return json.dumps({})


def parse_job_description(selected_job_title: str, df_jobs: pd.DataFrame) -> JobDescriptionInfo:
    """Fetches and parses the job description for the selected title using DeepSeek."""
    try:
        # Case-insensitive and whitespace-insensitive matching for job title
        job_row = df_jobs[df_jobs['Job Title'].str.strip().str.lower() == selected_job_title.strip().lower()]

        if job_row.empty:
            raise ValueError(f"Job title '{selected_job_title}' not found in the provided CSV.")

        # Get required and optional fields from CSV
        jd_text = job_row['Job Description'].iloc[0]
        company = job_row['Company'].iloc[0] if 'Company' in df_jobs.columns and pd.notna(job_row['Company'].iloc[0]) else None
        location = job_row['Location'].iloc[0] if 'Location' in df_jobs.columns and pd.notna(job_row['Location'].iloc[0]) else None

        if not jd_text or jd_text.isspace():
             raise ValueError(f"Job description text is empty for '{selected_job_title}'.")

        logger.info(f"Found job description for: {selected_job_title}. Calling LLM...")

        # Call DeepSeek LLM to parse the description text
        json_output_str = call_deepseek_for_jd_parsing(jd_text, selected_job_title)

        if not json_output_str or json_output_str == '{}':
             logger.error("Received empty or invalid JSON from DeepSeek JD parsing.")
             raise ValueError("LLM failed to parse job description, returned empty data.")

        # Parse the LLM JSON output using the Pydantic model
        parsed_data = json.loads(json_output_str)

        # --- Override/Supplement with data from CSV if LLM missed it ---
        # Ensure the selected job title is accurate
        parsed_data['job_title'] = selected_job_title # Always use the selected title
        if company and ('company' not in parsed_data or not parsed_data['company']):
             parsed_data['company'] = company
        if location and ('location' not in parsed_data or not parsed_data['location']):
             parsed_data['location'] = location
        # --- End Overrides ---

        jd_info = JobDescriptionInfo(**parsed_data)
        logger.info(f"Successfully parsed job description via DeepSeek for: {jd_info.job_title}")
        return jd_info

    except Exception as e:
        logger.error(f"Error parsing job description for {selected_job_title}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to parse job description '{selected_job_title}': {e}") from e