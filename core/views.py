from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import UserProfile, Post, Like, Comment, Follow, Bookmark, Notification, Story
from .forms import RegistrationForm, UserProfileForm, PostForm, CommentForm

def landing(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/landing.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            messages.success(request, "Registration successful! You can now log in.")
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'core/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('landing')

@login_required
def home(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, "Post published successfully!")
            return redirect('home')
    else:
        form = PostForm()

    # Get users we follow
    followed_users = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
    
    # Query feed posts (own posts + followed users' posts) using select_related
    posts = Post.objects.filter(
        Q(user__in=followed_users) | Q(user=request.user)
    ).select_related('user', 'user__profile').prefetch_related('likes', 'comments')

    # If the feed is empty, show all posts to make the platform feel alive and active
    if not posts.exists():
        posts = Post.objects.all().select_related('user', 'user__profile').prefetch_related('likes', 'comments')

    # Pagination for Infinite Scroll (5 posts per page)
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(posts, 5)
    page = request.GET.get('page')
    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'posts_html': ''})
        posts_page = paginator.page(paginator.num_pages)

    # Add interactive flags for frontend rendering
    for post in posts_page:
        post.is_liked_by_user = post.likes.filter(user=request.user).exists()
        post.is_bookmarked_by_user = Bookmark.objects.filter(user=request.user, post=post).exists()

    # Dynamic suggestions: users not followed and not self
    suggested_users = User.objects.exclude(
        id__in=followed_users
    ).exclude(id=request.user.id).select_related('profile')[:5]

    # Real Stories logic: Active stories in the last 24h
    import datetime
    from django.utils import timezone
    from collections import defaultdict
    import json

    active_stories = Story.objects.filter(
        created_at__gte=timezone.now() - datetime.timedelta(hours=24)
    ).select_related('user', 'user__profile').order_by('created_at')

    stories_by_user = defaultdict(list)
    for story in active_stories:
        stories_by_user[story.user].append({
            'id': story.id,
            'image_url': story.image.url if story.image else None,
            'video_url': story.video.url if story.video else None,
            'music_url': story.music.url if story.music else None,
            'caption': story.caption,
            'created_at': story.created_at.strftime('%I:%M %p')
        })

    story_bubbles = []
    story_bubbles_json = []
    for user, user_stories in stories_by_user.items():
        story_bubbles.append({
            'user': user,
            'stories': user_stories
        })
        story_bubbles_json.append({
            'username': user.username,
            'profile_pic': user.profile.profile_pic.url if user.profile.profile_pic else None,
            'stories': user_stories
        })

    # If AJAX scroll request, render the partial list of post cards
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/post_list_partial.html', {'posts': posts_page})

    context = {
        'form': form,
        'posts': posts_page,
        'suggested_users': suggested_users,
        'story_users': story_bubbles,
        'story_bubbles_json': json.dumps(story_bubbles_json),
    }
    return render(request, 'core/home.html', context)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('user', 'user__profile'), id=post_id)
    comments = post.comments.select_related('user', 'user__profile')
    is_liked = post.likes.filter(user=request.user).exists()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            messages.success(request, "Comment added.")
            return redirect('post_detail', post_id=post.id)
    else:
        form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'is_liked': is_liked,
        'form': form,
    }
    return render(request, 'core/post_detail.html', context)

@login_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete() # Unlike if already liked
            liked = False
        else:
            liked = True
            # Create Activity notification
            if post.user != request.user:
                Notification.objects.get_or_create(
                    sender=request.user, receiver=post.user, post=post, notification_type='like'
                )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'liked': liked,
                'likes_count': post.likes_count
            })
        
        # Redirect back to previous page
        next_url = request.META.get('HTTP_REFERER', 'home')
        return redirect(next_url)
    return redirect('home')

@login_required
def comment_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            
            # Create Activity notification
            if post.user != request.user:
                Notification.objects.create(
                    sender=request.user, receiver=post.user, post=post, notification_type='comment'
                )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                profile_pic_url = comment.user.profile.profile_pic.url if comment.user.profile.profile_pic else None
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': comment.id,
                        'username': comment.user.username,
                        'user_url': f'/user/{comment.user.username}/',
                        'profile_pic': profile_pic_url,
                        'content': comment.content,
                        'created_at': 'Just now'
                    }
                })
            messages.success(request, "Comment added.")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        
        next_url = request.META.get('HTTP_REFERER', 'post_detail')
        if next_url == 'post_detail':
            return redirect('post_detail', post_id=post.id)
        return redirect(next_url)
    return redirect('home')

@login_required
def user_profile(request, username):
    profile_user = get_object_or_404(User.objects.select_related('profile'), username=username)
    posts = profile_user.posts.all().prefetch_related('likes', 'comments')
    
    is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    
    # Check if we are viewing our own profile
    is_self = (request.user == profile_user)
    
    profile_form = None
    if is_self:
        if request.method == 'POST':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile_user.profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('user_profile', username=username)
        else:
            profile_form = UserProfileForm(instance=profile_user.profile)

    saved_posts = []
    if is_self:
        saved_posts = Post.objects.filter(bookmarks__user=profile_user).select_related('user', 'user__profile').prefetch_related('likes', 'comments')
        for post in saved_posts:
            post.is_liked_by_user = post.likes.filter(user=request.user).exists()
            post.is_bookmarked_by_user = True

    for post in posts:
        post.is_liked_by_user = post.likes.filter(user=request.user).exists()
        post.is_bookmarked_by_user = Bookmark.objects.filter(user=request.user, post=post).exists()

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'saved_posts': saved_posts,
        'is_following': is_following,
        'is_self': is_self,
        'profile_form': profile_form,
    }
    return render(request, 'core/user_profile.html', context)

@login_required
def follow_user(request, username):
    if request.method == 'POST':
        target_user = get_object_or_404(User, username=username)
        is_following = False
        if target_user != request.user:
            follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)
            if not created:
                follow.delete() # Unfollow
                is_following = False
            else:
                is_following = True
                # Create Activity notification
                Notification.objects.get_or_create(
                    sender=request.user, receiver=target_user, notification_type='follow'
                )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'following': is_following,
                'followers_count': target_user.profile.followers_count,
                'following_count': target_user.profile.following_count
            })

        next_url = request.META.get('HTTP_REFERER', 'user_profile')
        if 'user' in next_url:
            return redirect('user_profile', username=username)
        return redirect(next_url)
    return redirect('home')

@login_required
def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=profile_user).select_related('follower', 'follower__profile')
    
    # Check follow state for each follower from current user perspective
    for follow in followers:
        follow.follower.is_followed_by_user = Follow.objects.filter(follower=request.user, following=follow.follower).exists()
        
    context = {
        'profile_user': profile_user,
        'followers': followers,
    }
    return render(request, 'core/followers_list.html', context)

@login_required
def following_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    following_relations = Follow.objects.filter(follower=profile_user).select_related('following', 'following__profile')
    
    # Check follow state for each following user from current user perspective
    for relation in following_relations:
        relation.following.is_followed_by_user = Follow.objects.filter(follower=request.user, following=relation.following).exists()
        
    context = {
        'profile_user': profile_user,
        'following_relations': following_relations,
    }
    return render(request, 'core/following_list.html', context)

@login_required
def explore_view(request):
    query = request.GET.get('q', '').strip()
    users_results = []
    posts_results = []
    
    if query:
        users_results = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id).select_related('profile')
        
        posts_results = Post.objects.filter(
            caption__icontains=query
        ).select_related('user', 'user__profile').prefetch_related('likes', 'comments')
        
        for u in users_results:
            u.is_followed_by_user = Follow.objects.filter(follower=request.user, following=u).exists()
            
        for post in posts_results:
            post.is_liked_by_user = post.likes.filter(user=request.user).exists()
    else:
        from django.db.models import Count
        posts_results = Post.objects.annotate(
            num_likes=Count('likes')
        ).order_by('-num_likes', '-created_at').select_related('user', 'user__profile').prefetch_related('likes', 'comments')
        
        for post in posts_results:
            post.is_liked_by_user = post.likes.filter(user=request.user).exists()

    context = {
        'query': query,
        'users_results': users_results,
        'posts': posts_results,
    }
    return render(request, 'core/explore.html', context)

@login_required
def reels_view(request):
    # Filter posts that have a video file
    reels = Post.objects.exclude(video='').exclude(video__isnull=True).select_related('user', 'user__profile').prefetch_related('likes', 'comments')
    for post in reels:
        post.is_liked_by_user = post.likes.filter(user=request.user).exists()
        post.is_bookmarked_by_user = Bookmark.objects.filter(user=request.user, post=post).exists()
    return render(request, 'core/reels.html', {'posts': reels})

@login_required
def toggle_bookmark(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)
        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'bookmarked': bookmarked})
        
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    return redirect('home')

@login_required
def notifications_view(request):
    notifications = request.user.notifications.all().select_related('sender', 'sender__profile', 'post')
    # Mark all notifications as read when visiting
    notifications.update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifications})

@login_required
def delete_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        if post.user == request.user:
            post.delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, "Post deleted successfully.")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
            messages.error(request, "You cannot delete this post.")
    return redirect('home')

@login_required
def create_story_view(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        video = request.FILES.get('video')
        music = request.FILES.get('music')
        caption = request.POST.get('caption', '')
        
        if image or video:
            Story.objects.create(
                user=request.user,
                image=image,
                video=video,
                music=music,
                caption=caption
            )
            messages.success(request, "Story shared successfully!")
        else:
            messages.error(request, "You must upload either a photo or video to share a story.")
    return redirect('home')
