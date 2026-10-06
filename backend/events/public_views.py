import os

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from messaging.otp import request_otp, verify_otp

from .models import Guest
from .permissions import membership_role


class PublicEviteView(APIView):
    """Public guest page data for /evite/{uuid}.

    If the requester is event staff, includes an `admit` capability flag.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, guest_uuid):
        guest = get_object_or_404(Guest, uuid=guest_uuid)
        event = guest.event
        role = membership_role(request.user, event)
        return Response({
            'uuid': str(guest.uuid),
            'title': guest.title,
            'name': guest.name,
            'admits': guest.admits,
            'rsvp_status': guest.rsvp_status,
            'rsvp_count': guest.rsvp_count,
            'attended': guest.attended,
            'has_phone': bool(guest.phone),
            'can_admit': role is not None,
            'event': {
                'id': event.id,
                'name': event.name,
                'date_text': event.date_text,
                'venue': event.venue,
                'dress_code': event.dress_code,
            },
        })


class PublicRsvpView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, guest_uuid):
        guest = get_object_or_404(Guest, uuid=guest_uuid)
        status_value = request.data.get('status')
        if status_value not in (Guest.RSVP_ATTENDING, Guest.RSVP_DECLINED):
            return Response({'detail': "status must be 'attending' or "
                                       "'declined'."},
                            status=status.HTTP_400_BAD_REQUEST)
        count = request.data.get('count', 0)
        try:
            count = max(0, min(int(count), guest.admits))
        except (TypeError, ValueError):
            count = 0
        guest.rsvp_status = status_value
        guest.rsvp_count = count if status_value == Guest.RSVP_ATTENDING else 0
        guest.rsvp_at = timezone.now()
        guest.save(update_fields=['rsvp_status', 'rsvp_count', 'rsvp_at'])
        return Response({'rsvp_status': guest.rsvp_status,
                         'rsvp_count': guest.rsvp_count})


class PublicPdfView(APIView):
    """Download the generated card PDF."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, guest_uuid):
        guest = get_object_or_404(Guest, uuid=guest_uuid)
        if not guest.pdf_path:
            return Response({'detail': 'Card not generated yet.'},
                            status=status.HTTP_404_NOT_FOUND)
        path = os.path.join(settings.MEDIA_ROOT, guest.pdf_path)
        if not os.path.exists(path):
            return Response({'detail': 'Card file missing.'},
                            status=status.HTTP_404_NOT_FOUND)
        filename = f"{guest.name.replace(' ', '_')}_evite.pdf"
        return FileResponse(open(path, 'rb'), as_attachment=True,
                            filename=filename)


class PublicOtpRequestView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, guest_uuid):
        guest = get_object_or_404(Guest, uuid=guest_uuid)
        if guest.attended:
            return Response({'detail': 'Already verified.'})
        ok, detail = request_otp(guest)
        return Response({'detail': detail},
                        status=status.HTTP_200_OK if ok
                        else status.HTTP_400_BAD_REQUEST)


class PublicOtpVerifyView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, guest_uuid):
        guest = get_object_or_404(Guest, uuid=guest_uuid)
        if guest.attended:
            return Response({'detail': 'Already verified.',
                             'attended': True})
        code = request.data.get('code', '')
        if not code:
            return Response({'detail': 'code is required'},
                            status=status.HTTP_400_BAD_REQUEST)
        ok, detail = verify_otp(guest, code)
        return Response({'detail': detail, 'attended': ok},
                        status=status.HTTP_200_OK if ok
                        else status.HTTP_400_BAD_REQUEST)
