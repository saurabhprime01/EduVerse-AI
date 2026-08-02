from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from accounts.models import LearnerProfile, TopicProgress
from tutor.models import LearningJourneyNode, UserJourneyProgress
from activities.models import StudyPlan, StudyPlanItem

@login_required
def dashboard_view(request):
    # Ensure user has a profile
    try:
        profile = request.user.learner_profile
    except LearnerProfile.DoesNotExist:
        if request.user.role == 'parent':
            return redirect('accounts:parent_dashboard')
        profile = LearnerProfile.objects.create(user=request.user)

    # Streak logic
    today = date.today()
    if profile.last_active_date is None:
        profile.streak = 1
        profile.xp += 10 # Sign up bonus
        profile.coins += 5
    elif profile.last_active_date == today:
        pass
    elif (today - profile.last_active_date).days == 1:
        profile.streak += 1
        profile.xp += 15 # Daily streak reward
        profile.coins += 10
    else:
        profile.streak = 1
    
    profile.last_active_date = today
    profile.save()

    # Fetch daily checklist
    plan, created = StudyPlan.objects.get_or_create(profile=profile, target_date=today)
    if created:
        # Seed daily checklist tasks for a child
        StudyPlanItem.objects.create(plan=plan, task="Say hello to Buddy AI Tutor! 💬", xp_reward=10)
        StudyPlanItem.objects.create(plan=plan, task="Take an Adaptive Quiz! 📝", xp_reward=20)
        StudyPlanItem.objects.create(plan=plan, task="Practice Spaced Cards! 🎴", xp_reward=10)

    # Simple Recommendation Engine Logic
    # 1. Recommend based on weakest TopicProgress
    weakest_topic = TopicProgress.objects.filter(profile=profile).order_by('mastery_score').first()
    recommended_action = None
    
    if weakest_topic and weakest_topic.mastery_score < 70:
        recommended_action = {
            'type': 'topic_remedy',
            'subject': weakest_topic.subject,
            'topic': weakest_topic.topic,
            'title': f"Review {weakest_topic.topic} in {weakest_topic.subject}",
            'reason': f"Your Digital Twin shows we can boost your score here! (Current: {int(weakest_topic.mastery_score)}%)"
        }
    else:
        # 2. Or recommend next incomplete journey node
        completed_nodes = UserJourneyProgress.objects.filter(profile=profile, status='completed').values_list('node_id', flat=True)
        next_node = LearningJourneyNode.objects.exclude(id__in=completed_nodes).order_by('order').first()
        if next_node:
            recommended_action = {
                'type': 'journey_advance',
                'subject': next_node.subject,
                'topic': next_node.title,
                'title': f"Learn: {next_node.title}",
                'reason': "Ready for the next step in your map? Let's unlock this!"
            }
        else:
            # Fallback
            recommended_action = {
                'type': 'explore',
                'subject': 'math',
                'topic': 'Fractions',
                'title': "Talk to Buddy!",
                'reason': "Ask Buddy: 'Tell me a story about coding!'"
            }

    # Fetch Journey Node status list for visual rendering
    journey_progress = UserJourneyProgress.objects.filter(profile=profile)
    
    context = {
        'profile': profile,
        'plan': plan,
        'recommended_action': recommended_action,
        'journey_progress': journey_progress,
    }
    return render(request, 'core/dashboard.html', context)
