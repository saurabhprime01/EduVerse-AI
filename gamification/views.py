from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.models import LearnerProfile
from .models import RewardItem, UserRewardUnlock, UserAchievement, Notification

@login_required
def shop_view(request):
    profile = request.user.learner_profile

    # Seed shop items if empty
    if RewardItem.objects.count() == 0:
        RewardItem.objects.create(name="Classic Frame", description="A shiny classic badge frame for your avatar!", cost_coins=10, item_type='badge', asset_name='badge-classic')
        RewardItem.objects.create(name="Space Explorer (Dark)", description="Unlock the sleek, starry dark theme!", cost_coins=30, item_type='theme', asset_name='theme-dark')
        RewardItem.objects.create(name="Magic Kingdom (Purple)", description="A bright mystical purple theme!", cost_coins=45, item_type='theme', asset_name='theme-playful')
        RewardItem.objects.create(name="Wizard Buddy", description="Unlock the magic Wizard Buddy avatar!", cost_coins=60, item_type='avatar', asset_name='buddy_wizard')
        RewardItem.objects.create(name="Nature Green Buddy", description="Unlock the grassy leaf nature avatar!", cost_coins=40, item_type='avatar', asset_name='buddy_nature')

    all_rewards = RewardItem.objects.all()
    unlocked_ids = UserRewardUnlock.objects.filter(profile=profile).values_list('reward_id', flat=True)
    
    # Achievements list
    # Seed a basic achievement if none exist to make it colorful
    if UserAchievement.objects.filter(profile=profile).count() == 0:
        UserAchievement.objects.create(
            profile=profile,
            badge_name="First Step! 🚀",
            description="Created your profile in EduVerse!",
            icon_class="fa-rocket"
        )
    
    achievements = UserAchievement.objects.filter(profile=profile)

    context = {
        'profile': profile,
        'all_rewards': all_rewards,
        'unlocked_ids': list(unlocked_ids),
        'achievements': achievements,
    }
    return render(request, 'gamification/shop.html', context)

@login_required
def unlock_reward_api(request, item_id):
    if request.method == 'POST':
        profile = request.user.learner_profile
        reward = get_object_or_404(RewardItem, id=item_id)

        # Check if already unlocked
        already_unlocked = UserRewardUnlock.objects.filter(profile=profile, reward=reward).exists()
        if already_unlocked:
            return JsonResponse({'status': 'error', 'message': 'Already unlocked!'}, status=400)

        # Check coin cost
        if profile.coins < reward.cost_coins:
            return JsonResponse({'status': 'error', 'message': 'Not enough coins! Keep learning!'}, status=400)

        # Deduct coins and unlock
        profile.coins -= reward.cost_coins
        profile.save()

        UserRewardUnlock.objects.create(profile=profile, reward=reward)

        # Create alert notification
        Notification.objects.create(
            profile=profile,
            title="Item Unlocked! 🎉",
            message=f"You purchased: '{reward.name}'! Go to Settings to equip it.",
            type='reward'
        )

        # Auto grant achievement if they unlocked their first theme
        if reward.item_type == 'theme':
            UserAchievement.objects.get_or_create(
                profile=profile,
                badge_name="Theme Master 🎨",
                defaults={'description': "Unlocked a custom color theme in the Shop!", 'icon_class': 'fa-palette'}
            )

        return JsonResponse({
            'status': 'success',
            'coins_left': profile.coins,
            'message': f"Successfully unlocked {reward.name}!"
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid HTTP Method'}, status=405)
