from django.db.models import Count
from datetime import timedelta
from rest_framework import serializers
from django.utils import timezone
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    media_url = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    sender_username = serializers.SerializerMethodField()
    reply_to_message = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = "__all__"

    def get_media_url(self, obj):
        if not obj.media:
            return ""
        request = self.context.get("request") if self.context else None
        if request:
            return request.build_absolute_uri(obj.media.url)
        return obj.media.url

    def get_reactions(self, obj):
        qs = obj.reactions.values("emoji").annotate(count=Count("id")).order_by("emoji")
        return list(qs)

    def get_sender_username(self, obj):
        return obj.sender.username if getattr(obj, "sender", None) else ""

    def get_reply_to_message(self, obj):
        reply = getattr(obj, "reply_to", None)
        if not reply:
            return None
        return {
            "id": reply.id,
            "sender_id": reply.sender_id,
            "sender_username": reply.sender.username,
            "content": reply.content if not reply.is_deleted else "This message was deleted",
            "is_deleted": reply.is_deleted,
            "timestamp": reply.timestamp.isoformat() if reply.timestamp else None,
        }

    def _is_owner(self, obj):
        request = self.context.get("request") if self.context else None
        context_user = self.context.get("user") if self.context else None

        if request and request.user.is_authenticated:
            return obj.sender_id == request.user.id
        if context_user and getattr(context_user, "is_authenticated", False):
            return obj.sender_id == context_user.id
        return False

    def _is_within_edit_window(self, obj):
        if not obj.timestamp:
            return False
        return timezone.now() <= obj.timestamp + timedelta(minutes=30)

    def get_can_edit(self, obj):
        return self._is_owner(obj) and not obj.is_deleted and self._is_within_edit_window(obj)

    def get_can_delete(self, obj):
        return self._is_owner(obj) and not obj.is_deleted
