from rest_framework import serializers

from .models import Event, EventMember, Guest, SmsLog


class EventSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()
    guest_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = ('id', 'name', 'date_text', 'venue', 'dress_code',
                  'rsvp_contacts',
                  'card_bg_color', 'card_text_color', 'card_accent_color',
                  'artwork', 'artwork_crop', 'message_template',
                  'created_at', 'my_role', 'guest_count')

    def get_my_role(self, obj):
        from .permissions import membership_role
        return membership_role(self.context['request'].user, obj)


class EventMemberSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = EventMember
        fields = ('id', 'email', 'name', 'role', 'invited_email',
                  'created_at')

    def get_email(self, obj):
        return obj.user.email if obj.user else obj.invited_email

    def get_name(self, obj):
        return obj.user.name if obj.user else ''


class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = ('id', 'uuid', 'title', 'name', 'phone', 'phones',
                  'admits', 'rsvp_status', 'rsvp_count', 'rsvp_at',
                  'attended', 'attended_at', 'pdf_path', 'created_at')
        read_only_fields = ('uuid', 'rsvp_at', 'attended_at', 'pdf_path')


class SmsLogSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.name',
                                       read_only=True, default='')

    class Meta:
        model = SmsLog
        fields = ('id', 'guest', 'guest_name', 'phone', 'kind', 'status',
                  'api_response', 'sent_at')
