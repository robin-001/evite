import requests
from django.conf import settings


def send_sms(phone, message):
    """Send an SMS via the Kenkom gateway. Returns (ok, response_text)."""
    try:
        resp = requests.post(
            f"{settings.KENKOM_BASE_URL}/api/v1/sms/send/",
            headers={
                'x-api-key': settings.KENKOM_API_KEY,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            json={'phone': phone, 'message': message,
                  'sender': settings.KENKOM_SENDER},
            timeout=30,
        )
        return resp.status_code == 200, resp.text
    except Exception as e:
        return False, str(e)
