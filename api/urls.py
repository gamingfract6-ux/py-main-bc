from django.urls import path
from . import views
from .views import AuthenticateView, MeView

urlpatterns = [
    path('auth/authenticate', AuthenticateView.as_view(), name='authenticate'),
    path('auth/me', MeView.as_view(), name='me'),
    path('food/analyze', views.FoodAnalyzeView.as_view(), name='food_analyze'),
    path('food/history', views.HistoryView.as_view(), name='food_history'),
    path('food/scans/<int:pk>', views.FoodScanDetailView.as_view(), name='food-scan-detail'),
    path('chat', views.ChatView.as_view(), name='chat'),
    path('admin/check-ai', views.AdminCheckAIView.as_view(), name='admin_check_ai'),
]
