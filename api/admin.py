from django.contrib import admin
from .models import UserProfile, FoodScan, Feedback, ChatMessage

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'height', 'goal', 'lifestyle')
    search_fields = ('user__username', 'user__email')

@admin.register(FoodScan)
class FoodScanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'calories', 'protein', 'carbs', 'fats', 'timestamp')
    list_filter = ('timestamp', 'user')
    search_fields = ('user__username', 'user__email')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('scan', 'is_accurate', 'correct_food_name')
    list_filter = ('is_accurate',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_preview', 'timestamp')
    list_filter = ('timestamp', 'user')
    search_fields = ('user__username', 'user__email', 'message', 'response')

    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
