# face_recognition_app/serializers.py
from rest_framework import serializers
from .models import FaceEncoding

class FaceEncodingSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro del rostro de un usuario.
    """
    class Meta:
        model = FaceEncoding
        fields = ['user', 'profile_image', 'updated_at']
        read_only_fields = ['user', 'updated_at']
