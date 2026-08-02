from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Avg
from .models import LearnerProfile, TopicProgress, CustomUser
from .forms import SignUpForm, LearnerProfileSettingsForm
from tutor.models import AIConversationSession, LearningMemory
from activities.models import QuizSession

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}! Ready to learn?")
                return redirect('core:dashboard')
        messages.error(request, "Oops! Check your username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome to the EduVerse family! 🎉")
            return redirect('core:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Goodbye! See you next time! 👋")
    return redirect('accounts:login')

@login_required
def settings_view(request):
    try:
        profile = request.user.learner_profile
    except LearnerProfile.DoesNotExist:
        # If user is parent or admin, let's create a placeholder profile or redirect
        if request.user.role == 'parent':
            messages.info(request, "Parents can manage child settings from the Parent Room.")
            return redirect('accounts:parent_dashboard')
        profile = LearnerProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = LearnerProfileSettingsForm(request.POST, instance=profile)
        theme = request.POST.get('theme', 'theme-light')
        if form.is_valid():
            profile = form.save(commit=False)
            profile.selected_theme = theme
            profile.save()
            messages.success(request, "Settings updated successfully! ⚙️")
            return redirect('accounts:settings')
    else:
        form = LearnerProfileSettingsForm(instance=profile)
        
    context = {
        'form': form,
        'profile': profile,
        'themes': [
            ('theme-light', 'Sunny Skies (Light) ☀️'),
            ('theme-dark', 'Space Explorer (Dark) 🚀'),
            ('theme-playful', 'Magic Kingdom (Purple) 🦄'),
        ]
    }
    return render(request, 'accounts/settings.html', context)

@login_required
def parent_dashboard(request):
    # If child is logged in, they can't access parent room without entering a simple puzzle/parent pin or redirect.
    # We will support a list of children linked to this user (if parent) or default to request.user's own profile.
    if request.user.role == 'parent':
        children = request.user.children.all()
        selected_child = children.first() if children.exists() else None
    else:
        children = []
        selected_child = request.user

    # Fetch child profile
    profile = None
    if selected_child:
        try:
            profile = selected_child.learner_profile
        except LearnerProfile.DoesNotExist:
            profile = None

    if request.method == 'POST' and profile:
        # Parent changes child difficulty settings
        new_difficulty = request.POST.get('difficulty_level')
        if new_difficulty in ['beginner', 'intermediate', 'advanced']:
            profile.difficulty_level = new_difficulty
            profile.save()
            messages.success(request, f"Updated learning level to {profile.get_difficulty_level_display()}!")
            return redirect('accounts:parent_dashboard')

    # Metrics computation
    topics = TopicProgress.objects.filter(profile=profile) if profile else []
    strong_topics = [t for t in topics if t.mastery_score >= 75]
    weak_topics = [t for t in topics if t.mastery_score < 50]
    
    # AI Memory logs
    memories = LearningMemory.objects.filter(profile=profile) if profile else []
    
    # Recent chats
    chats = AIConversationSession.objects.filter(profile=profile).order_by('-created_at')[:5] if profile else []
    
    # Recent quizzes
    quizzes = QuizSession.objects.filter(profile=profile).order_by('-started_at')[:5] if profile else []

    # AI Pedagogical Advisor: Translate struggles into actionable parental tips
    parent_tips = []
    if profile:
        for m in memories:
            if m.category == 'struggle':
                key_lower = m.key.lower()
                if 'fraction' in key_lower or 'math' in key_lower:
                    parent_tips.append({
                        'topic': 'Mathematics',
                        'struggle': m.value,
                        'tip': "Slice oranges or cookies into halves, quarters, and eighths. Let your child eat 2/4 to visually realize it equals 1/2! Concrete objects help visual learners grasp abstract proportions."
                    })
                elif 'planet' in key_lower or 'space' in key_lower or 'solar' in key_lower or 'science' in key_lower:
                    parent_tips.append({
                        'topic': 'Science & Space',
                        'struggle': m.value,
                        'tip': "Draw concentric chalk circles on your driveway as planetary orbits. Have your child carry a planet marker and walk the orbits relative to a central Sun to feel orbital distances!"
                    })
                elif 'code' in key_lower or 'loop' in key_lower:
                    parent_tips.append({
                        'topic': 'Code Adventures',
                        'struggle': m.value,
                        'tip': "Play a game of Simon Says! Tell them: 'Repeat 3 times: Clap your hands and jump!' Explain that loops simply repeat steps without writing them out one-by-one."
                    })
                else:
                    parent_tips.append({
                        'topic': m.key.replace('_', ' ').title(),
                        'struggle': m.value,
                        'tip': "Ask your child to teach you what they learned today. Explaining a concept is the single best way to solidify their own understanding!"
                    })
                    
        # If no active struggles logged, return a generic recommendation
        if not parent_tips:
            parent_tips.append({
                'topic': 'General Progress',
                'struggle': 'No active struggles recorded yet.',
                'tip': "Keep encouraging curiosity! Have your child ask Buddy a 'Why' question today (e.g. 'Why is the sky blue?'). Asking questions builds early scientific reasoning."
            })

    context = {
        'children': children,
        'profile': profile,
        'topics': topics,
        'strong_topics': strong_topics,
        'weak_topics': weak_topics,
        'memories': memories,
        'chats': chats,
        'quizzes': quizzes,
        'parent_tips': parent_tips,
    }
    return render(request, 'accounts/parent_dashboard.html', context)
