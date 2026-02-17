from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    goal = models.CharField(max_length=100, null=True, blank=True)
    lifestyle = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email}'s profile"

class FoodScan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scans')
    image_url = models.CharField(max_length=500)
    food_items = models.JSONField()  # List of detected items
    calories = models.FloatField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fats = models.FloatField()
    meal_type = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.id} by {self.user.email}"

class Feedback(models.Model):
    scan = models.OneToOneField(FoodScan, on_delete=models.CASCADE, related_name='feedback')
    is_accurate = models.BooleanField()
    correct_food_name = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Feedback for Scan {self.scan_id}"

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat message by {self.user.email}"
