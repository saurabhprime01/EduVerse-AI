from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    # Quizzes
    path('quiz/', views.quiz_list, name='quiz_list'),
    path('quiz/start/<str:subject>/', views.quiz_start, name='quiz_start'),
    path('quiz/session/<int:session_id>/', views.quiz_active, name='quiz_active'),
    path('quiz/session/<int:session_id>/hint/<int:question_id>/', views.quiz_hint, name='quiz_hint'),
    path('quiz/session/<int:session_id>/submit/<int:question_id>/', views.quiz_submit, name='quiz_submit'),
    path('quiz/result/<int:session_id>/', views.quiz_result, name='quiz_result'),
    
    # Flashcards
    path('flashcards/', views.flashcard_list, name='flashcard_list'),
    path('flashcards/review/<int:card_id>/<int:score>/', views.flashcard_review_api, name='flashcard_review_api'),
    
    # Study Planner
    path('planner/', views.planner_view, name='planner'),
    path('planner/complete/<int:item_id>/', views.planner_complete_api, name='planner_complete_api'),
    
    # Code Lab
    path('codelab/', views.codelab_view, name='codelab'),
]
