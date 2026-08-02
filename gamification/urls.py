from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('shop/', views.shop_view, name='shop'),
    path('shop/unlock/<int:item_id>/', views.unlock_reward_api, name='unlock_reward_api'),
]
