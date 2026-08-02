from accounts.models import LearnerProfile

def learner_profile(request):
    if request.user.is_authenticated:
        try:
            profile = request.user.learner_profile
            return {'learner_profile': profile}
        except Exception:
            pass
    return {'learner_profile': None}
