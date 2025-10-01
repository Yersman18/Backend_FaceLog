# authentication/urls.py
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterStudentView,
    UserProfileView,
    CustomTokenObtainPairView,
    UserViewSet,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
    InstructorViewSet # Added InstructorViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'instructors', InstructorViewSet, basename='instructor') # Added InstructorViewSet

urlpatterns = [
    # Endpoint para registro de aprendices
    path('register/student/', RegisterStudentView.as_view(), name='register-student'),
    
    # Endpoints para autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoints para reseteo de contraseña
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='password-change'),
    
    # Endpoint para perfil de usuario
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Endpoints para gestión de usuarios por admin
    path('', include(router.urls)),
]