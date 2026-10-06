from django.urls import path

from . import public_views

urlpatterns = [
    path('evite/<uuid:guest_uuid>', public_views.PublicEviteView.as_view()),
    path('evite/<uuid:guest_uuid>/rsvp',
         public_views.PublicRsvpView.as_view()),
    path('evite/<uuid:guest_uuid>/pdf', public_views.PublicPdfView.as_view()),
    path('evite/<uuid:guest_uuid>/otp/request',
         public_views.PublicOtpRequestView.as_view()),
    path('evite/<uuid:guest_uuid>/otp/verify',
         public_views.PublicOtpVerifyView.as_view()),
]
