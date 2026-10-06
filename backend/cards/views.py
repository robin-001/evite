from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event, GenerationJob, Guest
from events.permissions import membership_role

from .services import generate_guest_pdf, render_card_html, start_generation_job


def _require_role(request, event, roles):
    if membership_role(request.user, event) not in roles:
        return Response({'detail': 'Not permitted.'},
                        status=status.HTTP_403_FORBIDDEN)
    return None


class GenerateView(APIView):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        denied = _require_role(request, event, ('owner', 'manager'))
        if denied:
            return denied
        running = event.generation_jobs.filter(
            status__in=(GenerationJob.STATUS_QUEUED,
                        GenerationJob.STATUS_RUNNING)).exists()
        if running:
            return Response({'detail': 'A generation job is already running.'},
                            status=status.HTTP_409_CONFLICT)
        job = start_generation_job(event)
        return Response({'job_id': job.id}, status=status.HTTP_202_ACCEPTED)


class GenerateStatusView(APIView):
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        denied = _require_role(
            request, event, ('owner', 'manager', 'scanner'))
        if denied:
            return denied
        job = event.generation_jobs.order_by('-created_at').first()
        if not job:
            return Response({'status': 'none'})
        return Response({
            'status': job.status, 'total': job.total, 'done': job.done,
            'error': job.error,
        })


class PreviewCardView(APIView):
    """GET renders the card HTML for inline preview; POST builds the PDF."""
    def get(self, request, pk, guest_id):
        event = get_object_or_404(Event, pk=pk)
        denied = _require_role(
            request, event, ('owner', 'manager', 'scanner'))
        if denied:
            return denied
        guest = get_object_or_404(Guest, pk=guest_id, event=event)
        return HttpResponse(render_card_html(guest))

    def post(self, request, pk, guest_id):
        event = get_object_or_404(Event, pk=pk)
        denied = _require_role(request, event, ('owner', 'manager'))
        if denied:
            return denied
        guest = get_object_or_404(Guest, pk=guest_id, event=event)
        generate_guest_pdf(guest)
        return Response({'pdf_path': guest.pdf_path})
