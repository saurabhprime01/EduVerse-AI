from django.urls import path
from . import views

app_name = 'tutor'

urlpatterns = [
    path('buddy/', views.buddy_view, name='buddy'),
    path('buddy/send/', views.send_message_api, name='send_message_api'),
    path('journey/', views.journey_view, name='journey'),
]
