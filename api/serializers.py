from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, FoodScan, Feedback, ChatMessage

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='first_name')
    profile_pic = serializers.SerializerMethodField()
    age = serializers.IntegerField(source='profile.age', read_only=True, default=28)
    height = serializers.FloatField(source='profile.height', read_only=True)
    weight = serializers.FloatField(source='profile.weight', read_only=True)
    gender = serializers.CharField(default="Male")
    fitness_goal = serializers.CharField(source='profile.goal', read_only=True)
    dietary_preference = serializers.CharField(source='profile.lifestyle', read_only=True)
    allergies = serializers.ListField(child=serializers.CharField(), default=lambda: ["Nuts", "Dairy"])
    region = serializers.CharField(default="India")
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'profile_pic', 'age', 'height', 'weight',
            'gender', 'fitness_goal', 'dietary_preference', 'allergies', 
            'region', 'created_at'
        ]

    def get_profile_pic(self, obj):
        return None

class FoodScanSerializer(serializers.ModelSerializer):
    total_calories = serializers.FloatField(source='calories', default=0.0)
    total_protein = serializers.FloatField(source='protein', default=0.0)
    total_carbs = serializers.FloatField(source='carbs', default=0.0)
    total_fats = serializers.FloatField(source='fats', default=0.0)
    total_fiber = serializers.FloatField(default=0.0)
    total_sugar = serializers.FloatField(default=0.0)
    total_sodium = serializers.FloatField(default=0.0)
    detected_foods = serializers.JSONField(source='food_items')
    confidence_score = serializers.FloatField(default=0.95)
    health_score = serializers.CharField(default="A")
    dietary_tags = serializers.ListField(child=serializers.CharField(), default=list)
    ai_insights = serializers.CharField(default="This meal looks balanced!")
    analysis_time = serializers.FloatField(default=1.2)
    created_at = serializers.DateTimeField(source='timestamp')

    class Meta:
        model = FoodScan
        fields = [
            'id', 'image_url', 'detected_foods', 
            'total_calories', 'total_protein', 'total_carbs', 'total_fats',
            'total_fiber', 'total_sugar', 'total_sodium',
            'confidence_score', 'health_score', 'dietary_tags', 
            'ai_insights', 'analysis_time', 'created_at', 'meal_type'
        ]

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'
