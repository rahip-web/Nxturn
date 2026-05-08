from django.urls import path
from .views import send_message, send_media, react_message, get_messages, unread_count, all_users, conversations, message_detail

urlpatterns = [
    path('send/<int:user_id>/', send_message),
    path('send-media/<int:user_id>/', send_media),
    path('message/<int:message_id>/', message_detail),
    path('react/', react_message),
    path('messages/<int:user_id>/', get_messages),
    path('unread-count/', unread_count),
    path('users/all/', all_users),
    path('conversations/', conversations),
]
 
