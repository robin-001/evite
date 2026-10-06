from django.urls import path

from cards import views as card_views
from messaging import views as messaging_views

from . import views

urlpatterns = [
    path('', views.EventListCreateView.as_view()),
    path('<int:pk>', views.EventDetailView.as_view()),
    path('<int:pk>/members', views.MemberListCreateView.as_view()),
    path('members/<int:pk>', views.MemberDetailView.as_view()),
    path('<int:pk>/guests', views.GuestListView.as_view()),
    path('guests/<int:pk>', views.GuestDeleteView.as_view()),
    path('<int:pk>/guests/import', views.GuestImportView.as_view()),
    path('<int:pk>/card', views.CardSettingsView.as_view()),
    path('<int:pk>/artwork', views.ArtworkUploadView.as_view()),
    path('<int:pk>/guests/<uuid:guest_uuid>/admit',
         views.AdmitGuestView.as_view()),
    path('<int:pk>/sms-log', views.SmsLogListView.as_view()),

    # cards app
    path('<int:pk>/generate', card_views.GenerateView.as_view()),
    path('<int:pk>/generate/status',
         card_views.GenerateStatusView.as_view()),
    path('<int:pk>/guests/<int:guest_id>/preview',
         card_views.PreviewCardView.as_view()),

    # messaging app
    path('<int:pk>/send', messaging_views.SendInvitesView.as_view()),
]
