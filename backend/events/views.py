from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event, EventMember, Guest, SmsLog
from .permissions import membership_role
from .serializers import (EventMemberSerializer, EventSerializer,
                          GuestSerializer, SmsLogSerializer)
from .utils import import_guests_csv

User = get_user_model()


class EventListCreateView(generics.ListCreateAPIView):
    serializer_class = EventSerializer

    def get_queryset(self):
        user = self.request.user
        return (Event.objects
                .filter(models_q(user))
                .annotate(guest_count=Count('guests'))
                .distinct())

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


def models_q(user):
    from django.db.models import Q
    return Q(owner=user) | Q(members__user=user)


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    def get_object(self):
        event = super().get_object()
        role = membership_role(self.request.user, event)
        if role is None:
            self.permission_denied(self.request)
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            if role != 'owner' and not (role == 'manager'
                                        and self.request.method == 'PATCH'):
                self.permission_denied(
                    self.request,
                    message='Only the owner or a manager can edit this event.')
            if self.request.method == 'DELETE' and role != 'owner':
                self.permission_denied(self.request,
                                       message='Only the owner can delete.')
        return event


class MemberListCreateView(generics.ListCreateAPIView):
    serializer_class = EventMemberSerializer

    def get_event(self):
        event = get_object_or_404(Event, pk=self.kwargs['pk'])
        if membership_role(self.request.user, event) != 'owner':
            self.permission_denied(self.request,
                                   message='Only the owner manages the team.')
        return event

    def get_queryset(self):
        return self.get_event().members.all()

    def perform_create(self, serializer):
        event = self.get_event()
        email = self.request.data.get('email', '').strip().lower()
        if not email:
            raise ValueError('email is required')
        user = User.objects.filter(email__iexact=email).first()
        serializer.save(event=event, user=user,
                        invited_email='' if user else email)


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EventMemberSerializer
    queryset = EventMember.objects.all()

    def get_object(self):
        member = super().get_object()
        if membership_role(self.request.user, member.event) != 'owner':
            self.permission_denied(self.request,
                                   message='Only the owner manages the team.')
        return member


class GuestListView(generics.ListAPIView):
    serializer_class = GuestSerializer

    def get_event(self):
        event = get_object_or_404(Event, pk=self.kwargs['pk'])
        if membership_role(self.request.user, event) is None:
            self.permission_denied(self.request)
        return event

    def get_queryset(self):
        return self.get_event().guests.all()


class GuestDeleteView(generics.DestroyAPIView):
    queryset = Guest.objects.all()

    def get_object(self):
        guest = super().get_object()
        if membership_role(self.request.user, guest.event) not in ('owner', 'manager'):
            self.permission_denied(self.request)
        return guest


class GuestImportView(APIView):
    """POST a CSV file (title,name,phone,admits) to bulk-import guests."""
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if membership_role(request.user, event) not in ('owner', 'manager'):
            return Response({'detail': 'Not permitted.'},
                            status=status.HTTP_403_FORBIDDEN)
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'file is required'},
                            status=status.HTTP_400_BAD_REQUEST)
        created, skipped = import_guests_csv(event, file_obj)
        return Response({'created': created,
                         'skipped': len(skipped)})


class CardSettingsView(APIView):
    """PATCH theme colors / message template on the event card."""

    def patch(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if membership_role(request.user, event) not in ('owner', 'manager'):
            return Response({'detail': 'Not permitted.'},
                            status=status.HTTP_403_FORBIDDEN)
        fields = ('card_bg_color', 'card_text_color', 'card_accent_color',
                  'message_template', 'artwork_crop', 'date_text', 'venue',
                  'dress_code', 'name', 'rsvp_contacts')
        for f in fields:
            if f in request.data:
                setattr(event, f, request.data[f])
        event.save()
        return Response(EventSerializer(event,
                                        context={'request': request}).data)


class ArtworkUploadView(APIView):
    """POST the card artwork image; optional crop JSON applies a PIL crop."""
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        if membership_role(request.user, event) not in ('owner', 'manager'):
            return Response({'detail': 'Not permitted.'},
                            status=status.HTTP_403_FORBIDDEN)
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'file is required'},
                            status=status.HTTP_400_BAD_REQUEST)
        event.artwork = file_obj
        event.save()
        return Response(EventSerializer(event,
                                        context={'request': request}).data)


class AdmitGuestView(APIView):
    """Staff (owner/manager/scanner) marks a guest as attended."""

    def post(self, request, pk, guest_uuid):
        event = get_object_or_404(Event, pk=pk)
        if membership_role(request.user, event) is None:
            return Response({'detail': 'Not permitted.'},
                            status=status.HTTP_403_FORBIDDEN)
        guest = get_object_or_404(Guest, uuid=guest_uuid, event=event)
        if guest.attended:
            return Response({'detail': 'Already admitted.',
                             'guest': GuestSerializer(guest).data})
        guest.attended = True
        guest.attended_at = timezone.now()
        guest.admitted_by = request.user
        guest.save(update_fields=['attended', 'attended_at', 'admitted_by'])
        return Response(GuestSerializer(guest).data)


class SmsLogListView(generics.ListAPIView):
    serializer_class = SmsLogSerializer

    def get_queryset(self):
        event = get_object_or_404(Event, pk=self.kwargs['pk'])
        if membership_role(self.request.user, event) is None:
            self.permission_denied(self.request)
        return SmsLog.objects.filter(guest__event=event).order_by('-sent_at')
