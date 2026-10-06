import uuid as uuid_lib

from django.conf import settings
from django.db import models


class Event(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='owned_events')
    name = models.CharField(max_length=200)
    date_text = models.CharField(max_length=120, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    dress_code = models.CharField(max_length=120, blank=True)
    # e.g. ["Lillian: +256 741 404 822", "Edmund: +256 787 467 287"]
    rsvp_contacts = models.JSONField(default=list, blank=True)

    # Card theme
    card_bg_color = models.CharField(max_length=20, default='#000000')
    card_text_color = models.CharField(max_length=20, default='#e3c388')
    card_accent_color = models.CharField(max_length=20, default='#e3c388')
    artwork = models.ImageField(upload_to='artwork/', blank=True)
    artwork_crop = models.JSONField(default=dict, blank=True)

    message_template = models.TextField(
        default="{name}, Join us to celebrate {event}. Your e-vite: {link}")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EventMember(models.Model):
    ROLE_MANAGER = 'manager'
    ROLE_SCANNER = 'scanner'
    ROLES = [(ROLE_MANAGER, 'Manager'), (ROLE_SCANNER, 'Scanner')]

    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             null=True, blank=True,
                             related_name='memberships')
    invited_email = models.EmailField(blank=True)  # pending invite
    role = models.CharField(max_length=20, choices=ROLES,
                            default=ROLE_SCANNER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'user'],
                                    name='unique_event_member'),
        ]

    def __str__(self):
        return f"{self.user or self.invited_email} @ {self.event}"


class Guest(models.Model):
    RSVP_PENDING = 'pending'
    RSVP_ATTENDING = 'attending'
    RSVP_DECLINED = 'declined'
    RSVP_CHOICES = [(RSVP_PENDING, 'Pending'),
                    (RSVP_ATTENDING, 'Attending'),
                    (RSVP_DECLINED, 'Declined')]

    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='guests')
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True,
                            editable=False)
    title = models.CharField(max_length=40, blank=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=40, blank=True)  # primary number
    phones = models.JSONField(default=list, blank=True)  # all numbers
    admits = models.PositiveIntegerField(default=1)

    rsvp_status = models.CharField(max_length=12, choices=RSVP_CHOICES,
                                   default=RSVP_PENDING)
    rsvp_count = models.PositiveIntegerField(default=0)
    rsvp_at = models.DateTimeField(null=True, blank=True)

    attended = models.BooleanField(default=False)
    attended_at = models.DateTimeField(null=True, blank=True)
    admitted_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='admissions')

    pdf_path = models.CharField(max_length=400, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} @ {self.event}"


class OtpToken(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE,
                              related_name='otp_tokens')
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class SmsLog(models.Model):
    KIND_INVITE = 'invite'
    KIND_OTP = 'otp'
    KIND_CHOICES = [(KIND_INVITE, 'Invite'), (KIND_OTP, 'OTP')]

    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL,
                              null=True, related_name='sms_logs')
    phone = models.CharField(max_length=40)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    status = models.CharField(max_length=12)  # sent | failed | dry_run
    api_response = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)


class GenerationJob(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(s, s.title()) for s in (
        STATUS_QUEUED, STATUS_RUNNING, STATUS_DONE, STATUS_FAILED)]

    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='generation_jobs')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default=STATUS_QUEUED)
    total = models.PositiveIntegerField(default=0)
    done = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
