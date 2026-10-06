from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    GoogleAuthSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def jwt_pair(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def attach_pending_memberships(user):
    """Attach event memberships that were invited to this email before signup."""
    from events.models import EventMember
    EventMember.objects.filter(
        invited_email__iexact=user.email, user__isnull=True
    ).update(user=user)


class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        attach_pending_memberships(user)
        return Response({**jwt_pair(user), 'user': UserSerializer(user).data},
                        status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['email'].lower(),
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response({'detail': 'Invalid email or password.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        attach_pending_memberships(user)
        return Response({**jwt_pair(user), 'user': UserSerializer(user).data})


class GoogleAuthView(APIView):
    """Verify a Google Identity Services credential and issue JWT."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not settings.GOOGLE_CLIENT_ID:
            return Response({'detail': 'Google sign-in is not configured.'},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token
            info = id_token.verify_oauth2_token(
                serializer.validated_data['credential'],
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError:
            return Response({'detail': 'Invalid Google credential.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        email = info.get('email', '').lower()
        if not email or not info.get('email_verified'):
            return Response({'detail': 'Google account has no verified email.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={'name': info.get('name', '')},
        )
        attach_pending_memberships(user)
        return Response({**jwt_pair(user), 'user': UserSerializer(user).data})


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
