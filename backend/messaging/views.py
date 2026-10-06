from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cards.services import public_url
from events.models import Event, SmsLog
from events.permissions import membership_role

from .kenkom import send_sms


def render_message(event, guest):
    """Render the event's message template for a guest."""
    title_name = f"{guest.title} {guest.name}".strip()
    first = f"{guest.title}. {guest.name.split()[0]}".strip() \
        if guest.title else guest.name.split()[0]
    return (event.message_template
            .replace('{title}', guest.title)
            .replace('{name}', guest.name)
            .replace('{first_name}', guest.name.split()[0])
            .replace('{greeting}', first)
            .replace('{event}', event.name)
            .replace('{link}', public_url(guest))
            .replace('{title_name}', title_name))


class SendInvitesView(APIView):
    """Send the invite SMS to every guest's number(s) via Kenkom."""

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if membership_role(request.user, event) not in ('owner', 'manager'):
            return Response({'detail': 'Not permitted.'},
                            status=status.HTTP_403_FORBIDDEN)
        if settings.SEND_SMS and not settings.KENKOM_API_KEY:
            return Response({'detail': 'KENKOM_API_KEY is not configured.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        sent, failed, dry, skipped = 0, 0, 0, 0
        for guest in event.guests.all():
            numbers = guest.phones or ([guest.phone] if guest.phone else [])
            if not numbers:
                skipped += 1
                continue
            message = render_message(event, guest)
            for number in numbers:
                if settings.SEND_SMS:
                    ok, resp = send_sms(number, message)
                    SmsLog.objects.create(
                        guest=guest, phone=number, kind=SmsLog.KIND_INVITE,
                        status='sent' if ok else 'failed',
                        api_response=resp)
                    sent += 1 if ok else 0
                    failed += 0 if ok else 1
                else:
                    SmsLog.objects.create(
                        guest=guest, phone=number, kind=SmsLog.KIND_INVITE,
                        status='dry_run', api_response=message)
                    dry += 1
        return Response({'live': settings.SEND_SMS, 'sent': sent,
                         'failed': failed, 'dry_run': dry,
                         'guests_without_phone': skipped})
