# matcher.py
from models import ResumeInfo, JobDescriptionInfo
import logging
import json
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

def call_deepseek_for_matching(resume_json: str, jd_json: str) -> tuple[float, str]:
    """Calls DeepSeek API for matching resume and JD, returning score and feedback."""
    logger.info("Calling DeepSeek API for matching and feedback...")
    default_response = 0.0, "Error: Could not generate matching results."

    if not DEEPSEEK_API_KEY:
        logger.error("DeepSeek API Key not found in environment variables.")
        return default_response

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    # Construct the prompt for comparison, scoring, and feedback
    prompt = f"""
    You are an expert HR recruitment assistant. Compare the following candidate resume JSON with the job description JSON.
    Focus ONLY on the requirements mentioned in the job description (skills, experience, education) and assess how well the candidate's resume aligns with these specific requirements. Ignore criteria present in the resume but not asked for in the job description.

    Based on this focused comparison, provide:
    1. A numerical match score as an integer percentage between 0 and 100 (e.g., 75).
    2. Constructive feedback text for the candidate (around 2-4 sentences).
       - If the match is good (e.g., score >= 65), highlight the matching strengths and mention any minor gaps positively.
       - If the match is poor (e.g., score < 65), provide positive feedback based on the candidate's general strengths evident in the resume, gently explain the key missing requirements for *this specific role*, and wish them luck.

    Return ONLY a single, valid JSON object containing two keys:
    - "match_score": The integer score (0-100).
    - "feedback": The textual feedback string.

    Do not include any extra text, explanations, or markdown formatting like ```json.

    Job Description JSON:
    {jd_json}

    Candidate Resume JSON:
    {resume_json}

    Valid JSON Output (with "match_score" and "feedback" keys only):
    """

    payload = {
        "model": DEEPSEEK_MODEL, # Use appropriate model, maybe a larger one for complex reasoning
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}, # Request JSON output
        "temperature": 0.5, # Allow some creativity in feedback, but keep score reasonable
        # "max_tokens": 512, # Adjust if needed for feedback length
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=90) # Longer timeout for analysis
        response.raise_for_status()
        response_data = response.json()

        if 'choices' in response_data and len(response_data['choices']) > 0:
            message_content = response_data['choices'][0].get('message', {}).get('content', '{}')
            try:
                # Attempt to parse the JSON response directly
                result_data = json.loads(message_content)
                score = float(result_data.get("match_score", 0)) # Default to 0 if missing
                feedback_text = result_data.get("feedback", "Feedback could not be generated.")

                # Basic validation of score
                if not 0 <= score <= 100:
                     logger.warning(f"DeepSeek returned an invalid score ({score}). Clamping to 0-100 range.")
                     score = max(0.0, min(100.0, score))

                logger.info(f"DeepSeek API call successful for matching. Score: {score}")
                return score, feedback_text

            except json.JSONDecodeError:
                logger.error(f"DeepSeek API returned invalid JSON for matching: {message_content[:500]}...")
                 # Attempt to extract JSON if wrapped in markdown
                if "```json" in message_content:
                    try:
                        extracted_json_str = message_content.split("```json")[1].split("```")[0].strip()
                        result_data = json.loads(extracted_json_str)
                        score = float(result_data.get("match_score", 0))
                        feedback_text = result_data.get("feedback", "Feedback could not be generated (extracted).")
                        if not 0 <= score <= 100: score = max(0.0, min(100.0, score)) # Clamp score
                        logger.info(f"Successfully extracted JSON wrapped in markdown (Matching). Score: {score}")
                        return score, feedback_text
                    except Exception as json_extract_error:
                        logger.error(f"Failed to extract JSON from markdown (Matching): {json_extract_error}")
                return default_response # Return default error response if invalid/extraction failed
            except Exception as parse_error:
                 logger.error(f"Error parsing valid JSON response content for matching: {parse_error}", exc_info=True)
                 return default_response
        else:
            logger.error(f"Unexpected response structure from DeepSeek API (matching): {response_data}")
            return default_response

    except requests.exceptions.Timeout:
        logger.error("DeepSeek API request timed out during matching.")
        return default_response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling DeepSeek API for matching: {e}", exc_info=True)
        return default_response
    except Exception as e:
        logger.error(f"An unexpected error occurred during DeepSeek matching call: {e}", exc_info=True)
        return default_response


def calculate_match_and_feedback(resume_info: ResumeInfo, jd_info: JobDescriptionInfo) -> tuple[float, str]:
    """
    Compares the resume and job description using DeepSeek API and returns score and feedback.
    """
    # Default error response matching the expected return type
    error_response = 0.0, "An error occurred during the matching process."
    try:
        # Convert Pydantic models to JSON strings for the LLM prompt
        # Ensure sensitive info potentially not needed for matching is excluded if necessary
        # e.g., resume_info.copy(exclude={'phone', 'misc'})
        resume_json_str = resume_info.json()
        jd_json_str = jd_info.json()

        match_score, feedback = call_deepseek_for_matching(resume_json_str, jd_json_str)

        logger.info(f"Matching complete via DeepSeek for {resume_info.candidate_name} and {jd_info.job_title}. Score: {match_score}")
        return match_score, feedback

    except Exception as e:
        logger.error(f"Error during matching preparation or calling DeepSeek: {e}", exc_info=True)
        # Provide default error values matching the expected tuple format
        return error_response