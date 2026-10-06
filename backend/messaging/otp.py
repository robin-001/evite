import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from events.models import OtpToken, SmsLog

from .kenkom import send_sms

MAX_ATTEMPTS = 5


def request_otp(guest):
    """Create an OTP for the guest and SMS it to their primary number.

    Returns (ok, detail).
    """
    if not guest.phone:
        return False, 'This invitation has no phone number on record.'

    # Resend cooldown
    latest = guest.otp_tokens.order_by('-created_at').first()
    if latest:
        age = (timezone.now() - latest.created_at).total_seconds()
        if age < settings.OTP_RESEND_COOLDOWN:
            wait = int(settings.OTP_RESEND_COOLDOWN - age)
            return False, f'Please wait {wait}s before requesting a new code.'

    guest.otp_tokens.filter(consumed=False).update(consumed=True)

    token = OtpToken.objects.create(
        guest=guest,
        code=f'{secrets.randbelow(1_000_000):06d}',
        expires_at=timezone.now() + timedelta(
            seconds=settings.OTP_TTL_SECONDS),
    )

    message = (f'Your {guest.event.name} verification code is '
               f'{token.code}. It expires in '
               f'{settings.OTP_TTL_SECONDS // 60} minutes.')

    if settings.SEND_SMS:
        ok, resp = send_sms(guest.phone, message)
        SmsLog.objects.create(
            guest=guest, phone=guest.phone, kind=SmsLog.KIND_OTP,
            status='sent' if ok else 'failed', api_response=resp)
        return (ok, 'Code sent.' if ok else 'Could not send the SMS.')
    SmsLog.objects.create(
        guest=guest, phone=guest.phone, kind=SmsLog.KIND_OTP,
        status='dry_run', api_response=message)
    return True, 'Code sent (dry run).'


def verify_otp(guest, code):
    """Check an OTP code. Returns (ok, detail). Marks the guest attended."""
    token = (guest.otp_tokens
             .filter(consumed=False)
             .order_by('-created_at').first())
    if not token:
        return False, 'No code was requested for this invitation.'
    if token.expires_at < timezone.now():
        return False, 'The code has expired. Request a new one.'
    if token.attempts >= MAX_ATTEMPTS:
        return False, 'Too many attempts. Request a new code.'
    if token.code != str(code).strip():
        token.attempts += 1
        token.save(update_fields=['attempts'])
        return False, 'Incorrect code.'
    token.consumed = True
    token.save(update_fields=['consumed'])
    guest.attended = True
    guest.attended_at = timezone.now()
    guest.save(update_fields=['attended', 'attended_at'])
    return True, 'Verified.'
