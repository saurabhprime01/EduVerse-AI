from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from accounts.models import LearnerProfile, TopicProgress
from .models import QuizSession, QuizQuestion, FlashcardDeck, FlashcardItem, StudyPlan, StudyPlanItem
from gamification.models import Notification

# Adaptive Question Bank
QUESTION_BANK = {
    'math': {
        'beginner': [
            {'q': "What is 5 + 3?", 'opts': ["7", "8", "9", "6"], 'ans': "8", 'hint': "Count forward 3 steps from 5!", 'exp': "5 + 3 equals 8."},
            {'q': "How many sides does a triangle have?", 'opts': ["3", "4", "5", "2"], 'ans': "3", 'hint': "Think of a slice of pizza or a wizard's hat!", 'exp': "A triangle always has 3 sides."}
        ],
        'intermediate': [
            {'q': "What is \\(\\frac{1}{2}\\) of 12?", 'opts': ["4", "6", "8", "5"], 'ans': "6", 'hint': "Sharing 12 cookies equally between 2 friends!", 'exp': "Half of 12 is 6 because 6 + 6 = 12."},
            {'q': "Which fraction is the largest?", 'opts': ["\\(\\frac{1}{4}\\)", "\\(\\frac{1}{2}\\)", "\\(\\frac{1}{8}\\)", "\\(\\frac{1}{3}\\)"], 'ans': "\\(\\frac{1}{2}\\)", 'hint': "Imagine sharing a cake. Is half a cake bigger than a quarter?", 'exp': "Dividing by a smaller number leaves a larger piece, so 1/2 is largest."}
        ],
        'advanced': [
            {'q': "Express 75% as a fraction.", 'opts': ["\\(\\frac{1}{2}\\)", "\\(\\frac{3}{4}\\)", "\\(\\frac{2}{3}\\)", "\\(\\frac{3}{5}\\)"], 'ans': "\\(\\frac{3}{4}\\)", 'hint': "Think of 75 cents out of a dollar. How many quarters is that?", 'exp': "75% is 75/100, which simplifies to 3/4."}
        ]
    },
    'science': {
        'beginner': [
            {'q': "Which star lights up our day?", 'opts': ["Moon", "Sun", "North Star", "Mars"], 'ans': "Sun", 'hint': "It is a giant yellow glowing ball in the sky!", 'exp': "The Sun is the star at the center of our solar system."}
        ],
        'intermediate': [
            {'q': "Which planet is known as the Red Planet?", 'opts': ["Venus", "Mars", "Jupiter", "Saturn"], 'ans': "Mars", 'hint': "It has rusty iron soil that makes it look reddish!", 'exp': "Mars is called the Red Planet because of iron oxide on its surface."}
        ],
        'advanced': [
            {'q': "What invisible force pulls objects down to Earth?", 'opts': ["Magnetism", "Gravity", "Friction", "Wind"], 'ans': "Gravity", 'hint': "It's why apples fall from trees instead of floating away!", 'exp': "Gravity is the force of attraction that pulls objects together."}
        ]
    },
    'english': {
        'beginner': [
            {'q': "Which word is an action word (verb)?", 'opts': ["Happy", "Run", "Apple", "Quickly"], 'ans': "Run", 'hint': "Something you do with your legs!", 'exp': "Run is a action, which makes it a verb."}
        ],
        'intermediate': [
            {'q': "Choose the correct spelling:", 'opts': ["Receive", "Recieve", "Receve", "Receivee"], 'ans': "Receive", 'hint': "Remember: 'I' before 'E', except after 'C'!", 'exp': "The correct spelling is Receive."}
        ],
        'advanced': [
            {'q': "What is the antonym (opposite) of 'Gargantuan'?", 'opts': ["Huge", "Tiny", "Heavy", "Ancient"], 'ans': "Tiny", 'hint': "Gargantuan means super-duper giant!", 'exp': "Gargantuan means enormous, so its opposite is tiny."}
        ]
    },
    'coding': {
        'beginner': [
            {'q': "What does HTML stand for?", 'opts': ["Hyper Text Markup Language", "High Tech Machine Logic", "Hyper Text Media Link", "Home Tool Markup Language"], 'ans': "Hyper Text Markup Language", 'hint': "It is the skeleton structure code of every website!", 'exp': "HTML stands for Hyper Text Markup Language."}
        ],
        'intermediate': [
            {'q': "How do we write a comment in HTML?", 'opts': ["// Comment", "<!-- Comment -->", "/* Comment */", "# Comment"], 'ans': "<!-- Comment -->", 'hint': "It starts with an exclamation and dashes!", 'exp': "HTML comments are written inside <!-- comment --> tags."}
        ],
        'advanced': [
            {'q': "What does a 'for loop' do in coding?", 'opts': ["Changes text color", "Repeats instructions", "Deletes files", "Saves a project"], 'ans': "Repeats instructions", 'hint': "Think of a loop that repeats until a count is reached!", 'exp': "For loops are used to repeat a block of code a set number of times."}
        ]
    }
}

@login_required
def quiz_list(request):
    try:
        profile = request.user.learner_profile
    except LearnerProfile.DoesNotExist:
        profile = LearnerProfile.objects.create(user=request.user)
        
    recent_quizzes = QuizSession.objects.filter(profile=profile, completed_at__isnull=False).order_by('-completed_at')[:5]
    
    context = {
        'profile': profile,
        'recent_quizzes': recent_quizzes,
        'subjects': [
            ('math', 'Mathematics 🔢'),
            ('science', 'Science & Space 🚀'),
            ('english', 'English & Grammar 📚'),
            ('coding', 'Coding Adventures 💻'),
        ]
    }
    return render(request, 'activities/quiz_list.html', context)

@login_required
def quiz_start(request, subject):
    profile = request.user.learner_profile
    
    # Create new quiz session
    session = QuizSession.objects.create(
        profile=profile,
        subject=subject,
        difficulty_used=profile.difficulty_level
    )
    
    # Seed the first question based on profile difficulty
    _generate_next_question(session, profile.difficulty_level)
    
    return redirect('activities:quiz_active', session_id=session.id)

@login_required
def quiz_active(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, profile__user=request.user)
    
    # Check if quiz is already completed
    if session.completed_at:
        return redirect('activities:quiz_result', session_id=session.id)
        
    # Get current unanswered question
    current_q = session.questions.filter(user_answer__isnull=True).first()
    
    if not current_q:
        # If there are already 5 questions, complete quiz!
        if session.questions.all().count() >= 5:
            return _complete_quiz(session)
        else:
            # Generate next question adaptively based on last correctness!
            last_q = session.questions.all().order_by('id').last()
            next_diff = session.difficulty_used
            
            if last_q:
                if last_q.is_correct:
                    # Upgrade difficulty
                    if last_q.difficulty == 'beginner':
                        next_diff = 'intermediate'
                    elif last_q.difficulty == 'intermediate':
                        next_diff = 'advanced'
                else:
                    # Downgrade difficulty
                    if last_q.difficulty == 'advanced':
                        next_diff = 'intermediate'
                    elif last_q.difficulty == 'intermediate':
                        next_diff = 'beginner'
            
            _generate_next_question(session, next_diff)
            current_q = session.questions.filter(user_answer__isnull=True).first()
            
    question_index = list(session.questions.all().order_by('id')).index(current_q) + 1

    context = {
        'session': session,
        'question': current_q,
        'question_index': question_index,
    }
    return render(request, 'activities/quiz_active.html', context)

@login_required
def quiz_hint(request, session_id, question_id):
    question = get_object_or_404(QuizQuestion, id=question_id, session__profile__user=request.user)
    return JsonResponse({'status': 'success', 'hint': question.hint})

@login_required
def quiz_submit(request, session_id, question_id):
    if request.method == 'POST':
        question = get_object_or_404(QuizQuestion, id=question_id, session__profile__user=request.user)
        user_choice = request.POST.get('choice')
        
        if not user_choice:
            return redirect('activities:quiz_active', session_id=session_id)
            
        question.user_answer = user_choice
        question.is_correct = (user_choice == question.correct_answer)
        question.save()
        
        # Immediate small reward to motivate
        profile = request.user.learner_profile
        if question.is_correct:
            profile.xp += 10
            profile.coins += 2
        else:
            profile.xp += 2 # Consolation prize
        profile.save()
        
        return render(request, 'activities/quiz_feedback.html', {
            'session': question.session,
            'question': question,
            'is_correct': question.is_correct
        })
        
    return redirect('activities:quiz_active', session_id=session_id)

@login_required
def quiz_result(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, profile__user=request.user)
    return render(request, 'activities/quiz_result.html', {'session': session})


# Spaced Repetition (SuperMemo-2 SM-2 Algorithm) Flashcards review
@login_required
def flashcard_list(request):
    profile = request.user.learner_profile
    
    # Seed default deck if none exists
    deck, created = FlashcardDeck.objects.get_or_create(
        profile=profile,
        title="My Spaced Cards 🎴",
        subject="general"
    )
    if created or deck.cards.count() == 0:
        # Seed 3 card items
        FlashcardItem.objects.create(
            deck=deck,
            front="What is a Fraction? 🍕",
            back="A fraction tells us how many parts of a whole we have. For example, half a pizza is 1/2!",
            hint="Slicing a whole cake into pieces!"
        )
        FlashcardItem.objects.create(
            deck=deck,
            front="What is Gravity? 🌎",
            back="Gravity is an invisible pull force that keeps our feet on the ground and planets orbiting the Sun.",
            hint="The apple falling on Newton's head!"
        )
        FlashcardItem.objects.create(
            deck=deck,
            front="What is a Loop in coding? 🔄",
            back="A loop is an instruction that repeats a block of code over and over until it is told to stop.",
            hint="Doing circles until you are done!"
        )

    # Fetch cards scheduled for review today or earlier
    today_date = date.today()
    cards_to_review = FlashcardItem.objects.filter(deck__profile=profile, next_review__lte=today_date)
    all_cards = FlashcardItem.objects.filter(deck__profile=profile)

    context = {
        'profile': profile,
        'cards_to_review': cards_to_review,
        'all_cards': all_cards,
    }
    return render(request, 'activities/flashcards.html', context)

@login_required
def flashcard_review_api(request, card_id, score):
    """
    Apply SM-2 Algorithm based on child's self-rating score (1-5):
    1 = Forgot (hardest)
    3 = Remembered with effort
    5 = Super easy (easiest)
    """
    card = get_object_or_404(FlashcardItem, id=card_id, deck__profile__user=request.user)
    
    # SM-2 Spaced repetition logic
    if score >= 3:
        if card.interval == 1:
            card.interval = 6
        elif card.interval == 6:
            card.interval = 12
        else:
            card.interval = int(card.interval * card.ease_factor)
    else:
        card.interval = 1
        
    # Update ease factor
    card.ease_factor = card.ease_factor + (0.1 - (5 - score) * (0.08 + (5 - score) * 0.02))
    if card.ease_factor < 1.3:
        card.ease_factor = 1.3
        
    card.next_review = date.today() + timedelta(days=card.interval)
    card.save()

    # Reward XP
    profile = request.user.learner_profile
    profile.xp += 5
    profile.coins += 1
    profile.save()

    return JsonResponse({
        'status': 'success',
        'next_review_days': card.interval,
        'xp_earned': 5
    })


# Study Planner
@login_required
def planner_view(request):
    profile = request.user.learner_profile
    today = date.today()
    plan, created = StudyPlan.objects.get_or_create(profile=profile, target_date=today)
    
    context = {
        'profile': profile,
        'plan': plan,
    }
    return render(request, 'activities/planner.html', context)

@login_required
def planner_complete_api(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(StudyPlanItem, id=item_id, plan__profile__user=request.user)
        if not item.is_done:
            item.is_done = True
            item.save()
            
            # Reward
            profile = request.user.learner_profile
            profile.xp += item.xp_reward
            profile.coins += 5
            profile.save()

            # Create notification
            Notification.objects.create(
                profile=profile,
                title="Challenge Completed! 🏆",
                message=f"You completed: '{item.task}' and won 5 coins!",
                type='achievement'
            )
            
            return JsonResponse({
                'status': 'success',
                'xp_gained': item.xp_reward,
                'coins_gained': 5
            })
        return JsonResponse({'status': 'error', 'message': 'Already completed'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid HTTP Method'}, status=405)


# Code Lab View
@login_required
def codelab_view(request):
    return render(request, 'activities/codelab.html')


# Helpers
def _generate_next_question(session, diff):
    subject = session.subject
    q_pool = QUESTION_BANK.get(subject, {}).get(diff, [])
    
    if not q_pool:
        # Fallback to general math beginner if subject is wrong
        q_pool = QUESTION_BANK['math']['beginner']
        
    import random
    selected = random.choice(q_pool)
    
    # Avoid duplicate questions in the same session if possible
    existing_texts = session.questions.values_list('question_text', flat=True)
    if selected['q'] in existing_texts and len(q_pool) > 1:
        selected = [q for q in q_pool if q['q'] not in existing_texts][0]
        
    QuizQuestion.objects.create(
        session=session,
        question_text=selected['q'],
        options=selected['opts'],
        hint=selected['hint'],
        explanation=selected['exp'],
        correct_answer=selected['ans'],
        difficulty=diff
    )

def _complete_quiz(session):
    session.completed_at = timezone.now()
    
    total = session.questions.all().count()
    corrects = session.questions.filter(is_correct=True).count()
    session.score = (corrects / total) * 100.0 if total > 0 else 0
    session.save()
    
    # Substantial Completion rewards
    profile = session.profile
    xp_bonus = 30 + (20 if session.score == 100 else 0)
    coin_bonus = 10 + (10 if session.score == 100 else 0)
    
    profile.xp += xp_bonus
    profile.coins += coin_bonus
    profile.save()
    
    # Create global achievements if they got 100%
    if session.score == 100:
        Notification.objects.create(
            profile=profile,
            title="Perfect Quiz Score! 🎓",
            message=f"Outstanding! You scored 100% on the {session.subject|title} Quiz!",
            type='achievement'
        )

    # Sync mastery to TopicProgress Digital Twin
    TopicProgress.objects.update_or_create(
        profile=profile,
        subject=session.subject,
        topic=f"Quiz Assessment",
        defaults={
            'mastery_score': session.score,
            'confidence': session.score
        }
    )

    return redirect('activities:quiz_result', session_id=session.id)
