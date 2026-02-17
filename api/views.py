from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, authentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate as dj_authenticate
from django.conf import settings
from django.shortcuts import render
from .models import FoodScan, Feedback, ChatMessage
from .serializers import FoodScanSerializer, ChatMessageSerializer, UserSerializer
from . import utils
import os
import datetime
import shutil
class AuthenticateView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print(f"DEBUG: AuthenticateView.post called with data: {request.data}")
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name', '')

        if not email or not password:
            return Response({"error": "Email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        
        if user:
            # User exists, check password
            if not user.check_password(password):
                return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # Register new user
            username = email.split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'bearer',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}".strip() or user.username
            }
        })

class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        print(f"DEBUG: MeView.get_object called for user: {self.request.user}")
        return self.request.user

class FoodAnalyzeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print("DEBUG: FoodAnalyzeView.post called")
        image = request.FILES.get('image')
        if not image:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Save file locally
        os.makedirs("media/scans", exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{image.name}"
        file_path = os.path.join("media/scans", filename)
        
        with open(file_path, "wb") as buffer:
            for chunk in image.chunks():
                buffer.write(chunk)
        
        print(f"DEBUG: Processing image: {image.name} ({image.content_type})")
        print(f"DEBUG: Saved to: {file_path}")
        
        # Read image data for Gemini
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        print(f"DEBUG: Read {len(image_bytes)} bytes")
        
        # Call AI Analysis (Sync)
        print("DEBUG: Sending to Gemini AI...")
        analysis_result = utils.analyze_food_image(image_bytes, image.content_type)
        print(f"DEBUG: AI Result: {analysis_result}")
        
        if not analysis_result or "error" in analysis_result:
            print(f"DEBUG: Analysis failed with error: {analysis_result.get('error')}")
            return Response({"error": analysis_result.get("error", "Analysis failed")}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save scan to database
        scan = FoodScan.objects.create(
            user=request.user,
            image_url=request.build_absolute_uri(settings.MEDIA_URL + f"scans/{filename}"),
            food_items=analysis_result.get("items", []),
            calories=analysis_result.get("calories", 0),
            protein=analysis_result.get("protein", 0),
            carbs=analysis_result.get("carbs", 0),
            fats=analysis_result.get("fats", 0)
        )
        
        # Add AI results to scan context for serializer defaults if needed
        # Actually, let's pass them to serializer or just return the serialized data
        serializer = FoodScanSerializer(scan)
        response_data = serializer.data
        
        # Override fields from AI result that are not in the model but needed by frontend
        response_data.update({
            "health_score": analysis_result.get("health_score", "B"),
            "dietary_tags": analysis_result.get("dietary_tags", []),
            "ai_insights": analysis_result.get("ai_insights", "Your meal is analyzed."),
        })

        print(f"DEBUG: Final Response Data: {response_data}")
        return Response(response_data, status=status.HTTP_201_CREATED)

class HistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        print(f"DEBUG: HistoryView.get called for user: {request.user}")
        scans = FoodScan.objects.filter(user=request.user).order_by('-timestamp')
        serializer = FoodScanSerializer(scans, many=True)
        return Response(serializer.data)

class FoodScanDetailView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FoodScanSerializer
    queryset = FoodScan.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        print(f"DEBUG: ChatView.get called for user: {request.user}")
        messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        print(f"DEBUG: ChatView.post called with data: {request.data}")
        message = request.data.get('message')
        if not message:
            return Response({"error": "No message provided"}, status=status.HTTP_400_BAD_REQUEST)

        ai_response = utils.get_ai_coach_response(message)
        
        # Save to DB
        ChatMessage.objects.create(
            user=request.user,
            message=message,
            response=ai_response
        )
        
        return Response({"response": ai_response})

class AdminCheckAIView(APIView):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return render(request, 'api/check_ai.html')

    def post(self, request):
        print(f"DEBUG: AdminCheckAIView.post called with data: {request.data}")
        api_key = request.data.get('api_key')
        result = utils.test_gemini_connection(api_key)
        return Response(result)
