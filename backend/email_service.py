
import os
import resend
from dotenv import load_dotenv

load_dotenv()


def send_email(to_email: str, subject: str, body: str) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")

    if not api_key or not from_email:
        raise RuntimeError(
            "RESEND_API_KEY or RESEND_FROM_EMAIL is missing in .env"
        )

    resend.api_key = api_key

    params = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body,
    }

    response = resend.Emails.send(params)
    print("Resend response:", response)
    return True
