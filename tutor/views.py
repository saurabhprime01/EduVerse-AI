from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.models import LearnerProfile
from .models import AIConversationSession, AIConversationMessage
from .services import GeminiTutorService
import re

@login_required
def buddy_view(request):
    try:
        profile = request.user.learner_profile
    except LearnerProfile.DoesNotExist:
        profile = LearnerProfile.objects.create(user=request.user)

    subject = request.GET.get('subject', 'general')
    topic = request.GET.get('topic', 'Learning Together')

    # Get or create active session for this subject
    session = AIConversationSession.objects.filter(profile=profile, subject=subject, is_active=True).order_by('-created_at').first()
    
    if not session:
        session = AIConversationSession.objects.create(
            profile=profile,
            subject=subject,
            title=f"Learning about {topic}"
        )
        # Create an initial warm welcoming message from Buddy
        welcome_text = f"Hey {request.user.username}! I am Buddy, your AI tutor. Today, let's explore {topic}! 🚀 I'm ready, are you? Ask me anything, or click the mic to speak!"
        AIConversationMessage.objects.create(
            session=session,
            sender='ai',
            text=welcome_text
        )

    # Fetch last 30 messages in the chat session
    messages = session.messages.all().order_by('timestamp')[:30]

    context = {
        'session': session,
        'chat_messages': messages,
        'active_subject': subject,
        'active_topic': topic,
        'profile': profile
    }
    return render(request, 'tutor/buddy.html', context)

@login_required
def send_message_api(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        message_text = request.POST.get('message_text', '').strip()
        
        if not message_text:
            return JsonResponse({'status': 'error', 'message': 'Empty message'}, status=400)
            
        session = get_object_or_404(AIConversationSession, id=session_id, profile__user=request.user)
        
        # 1. Save user message
        AIConversationMessage.objects.create(
            session=session,
            sender='child',
            text=message_text
        )
        # 2. Call service layer
        tutor_service = GeminiTutorService()
        ai_response, visual_data = tutor_service.generate_tutor_response(session, message_text)

        # 3. Save AI response
        AIConversationMessage.objects.create(
            session=session,
            sender='ai',
            text=ai_response,
            visual_explanations=visual_data or {}
        )
        
        return JsonResponse({
            'status': 'success',
            'ai_response': ai_response,
            'visual_data': visual_data
        })
        
    return JsonResponse({'status': 'error', 'message': 'Invalid HTTP Method'}, status=405)

@login_required
def journey_view(request):
    # Simply renders the journey visual path selection page
    return render(request, 'tutor/journey.html')
