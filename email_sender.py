# email_sender.py
import smtplib
from email.message import EmailMessage
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# --- Email Configuration (Load from .env) ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com") # Default to Gmail
SMTP_PORT = int(os.getenv("SMTP_PORT", 587)) # Default TLS port
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") # Use App Password for Gmail

def send_application_email(
    to_email: str,
    candidate_name: str,
    job_title: str,
    match_score: float,
    feedback: str
):
    """Sends an email to the candidate based on the match score."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        logger.error("Email sender credentials (EMAIL_SENDER, EMAIL_PASSWORD) not found in environment variables. Cannot send email.")
        return False # Indicate failure

    if not to_email:
         logger.warning(f"No email address found for candidate {candidate_name}. Skipping email.")
         return False

    is_qualified = match_score >= 65.0

    # --- Customize Email Content ---
    if is_qualified:
        subject = f"Congratulations regarding your application for {job_title}!"
        body = f"""
Dear {candidate_name or 'Candidate'},

Congratulations! We were impressed with your resume and qualifications for the {job_title} position (Match Score: {match_score:.1f}%).

Our recruitment team believes you could be a strong fit. Here is some initial feedback based on our automated review:
{feedback}

We would like to invite you to the next stage of the application process. [Optional: Add details about next steps, e.g., scheduling an interview, link to assessment, etc.].

We will be in touch soon with further details.

Best regards,
[Your Company Name] Recruitment Team
        """
    else:
        subject = f"Update regarding your application for {job_title}"
        body = f"""
Dear {candidate_name or 'Candidate'},

Thank you for your interest in the {job_title} position at [Your Company Name] and for taking the time to apply.

We received a large number of applications, and after careful review, we have decided not to move forward with your candidacy for this specific role at this time.

Our automated system provided the following feedback based on your resume against the job requirements (Match Score: {match_score:.1f}%):
{feedback}

We appreciate your interest in our company and encourage you to keep an eye on our careers page for future opportunities that may be a better fit.

We wish you the best in your job search.

Sincerely,
[Your Company Name] Recruitment Team
        """
    # --- End Email Content ---

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg.set_content(body)

    try:
        logger.info(f"Attempting to send {'congratulatory' if is_qualified else 'rejection'} email to {to_email} for {job_title}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"Email successfully sent to {to_email}")
        return True # Indicate success
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP Authentication Error: Check EMAIL_SENDER and EMAIL_PASSWORD (use App Password for Gmail).")
        return False
    except smtplib.SMTPServerDisconnected:
         logger.error("SMTP server disconnected unexpectedly. Check server address/port or network.")
         return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error sending email to {to_email}: {e}", exc_info=True)
        return False
    except Exception as e:
         logger.error(f"An unexpected error occurred during email sending to {to_email}: {e}", exc_info=True)
         return False

# Example Usage (for testing)
# if __name__ == "__main__":
#     # Make sure .env file exists and has credentials
#     test_email = "recipient@example.com" # Replace with a test recipient
#     test_name = "Test Candidate"
#     test_job = "Tester Role"
#     test_score_good = 70.0
#     test_score_bad = 55.0
#     test_feedback = "This is test feedback."
#
#     print("Testing good score email...")
#     send_application_email(test_email, test_name, test_job, test_score_good, test_feedback)
#     print("\nTesting bad score email...")
#     send_application_email(test_email, test_name, test_job, test_score_bad, test_feedback)