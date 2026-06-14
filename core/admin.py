from django.contrib import admin
from .models import UserProfile, Post, Like, Comment, Follow, Bookmark, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'followers_count', 'following_count')
    search_fields = ('user__username', 'bio')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'likes_count', 'comments_count')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'caption')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'content')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'sender', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
