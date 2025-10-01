# face_recognition_app/urls.py
from django.urls import path
from .views import FacialRegistrationView, FacialRecognitionView

urlpatterns = [
    # Endpoint para que un estudiante registre su rostro
    path('register/', FacialRegistrationView.as_view(), name='facial-registration'),
    
    # Endpoint para el proceso de reconocimiento en tiempo real
    path('recognize/', FacialRecognitionView.as_view(), name='facial-recognition'),
]