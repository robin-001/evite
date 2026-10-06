import base64
import io
import os
import threading

import qrcode
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from events.models import GenerationJob, Guest


def qr_data_url(url):
    """Return a data-URL PNG QR for the given URL."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L,
                     box_size=10, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def public_url(guest):
    return f"{settings.PUBLIC_BASE_URL}/evite/{guest.uuid}"


def guest_title_line(guest):
    return f"{guest.title} {guest.name}".strip()


def render_card_html(guest):
    """Render the card HTML for a guest using the event's theme."""
    event = guest.event
    artwork_url = ''
    if event.artwork:
        try:
            with open(event.artwork.path, 'rb') as f:
                artwork_url = 'data:image/jpeg;base64,' + \
                    base64.b64encode(f.read()).decode()
        except (ValueError, FileNotFoundError):
            artwork_url = ''
    return render_to_string('cards/card.html', {
        'event': event,
        'guest': guest,
        'greeting': f"Dear {guest_title_line(guest)}",
        'qr_data_url': qr_data_url(public_url(guest)),
        'artwork_url': artwork_url,
        'address': 'UHMG Complex, 2nd Floor, Martyrs Crescent Ntinda, Kampala',
        'brand_email': 'info@angstrom-technologies.ug',
        'brand_site': 'events.angstrom-technologies.ug',
    })


def card_pdf_path(guest):
    """Storage path for the guest's PDF, named by the short uuid."""
    return os.path.join(
        settings.MEDIA_ROOT, 'events', str(guest.event_id),
        'cards', f"{str(guest.uuid).split('-')[0]}.pdf")


_browser_lock = threading.Lock()


def _render_pdf(html, out_path):
    from playwright.sync_api import sync_playwright
    with _browser_lock, sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html, wait_until='load')
            page.pdf(path=out_path, format='Letter',
                     print_background=True,
                     margin={'top': '0', 'bottom': '0',
                             'left': '0', 'right': '0'})
        finally:
            browser.close()


def generate_guest_pdf(guest):
    html = render_card_html(guest)
    out = card_pdf_path(guest)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    _render_pdf(html, out)
    guest.pdf_path = os.path.relpath(out, settings.MEDIA_ROOT).replace('\\', '/')
    guest.save(update_fields=['pdf_path'])
    return out


def run_generation_job(job_id):
    """Background thread: generate a PDF card for every guest."""
    job = GenerationJob.objects.get(pk=job_id)
    job.status = GenerationJob.STATUS_RUNNING
    job.save(update_fields=['status'])
    try:
        guests = list(Guest.objects.filter(event=job.event))
        job.total = len(guests)
        job.save(update_fields=['total'])
        for guest in guests:
            generate_guest_pdf(guest)
            job.done += 1
            job.save(update_fields=['done'])
        job.status = GenerationJob.STATUS_DONE
    except Exception as e:
        job.status = GenerationJob.STATUS_FAILED
        job.error = str(e)
    job.finished_at = timezone.now()
    job.save()


def start_generation_job(event):
    job = GenerationJob.objects.create(event=event)
    threading.Thread(target=run_generation_job,
                     args=(job.id,), daemon=True).start()
    return job
