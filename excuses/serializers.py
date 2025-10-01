# excuses/serializers.py
from django.urls import reverse
from rest_framework import serializers
from .models import Excuse
from attendance.serializers import SimpleUserSerializer, AttendanceSessionSerializer

class ExcuseSerializer(serializers.ModelSerializer):
    """
    Serializador para la creación y visualización de excusas.
    """
    student = SimpleUserSerializer(read_only=True)
    session = AttendanceSessionSerializer(read_only=True)
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Excuse
        fields = ['id', 'student', 'session', 'reason', 'document', 'document_url', 'status', 'reviewed_by', 'review_comment', 'created_at', 'reviewed_at']
        read_only_fields = ['id', 'status', 'reviewed_by', 'review_comment', 'created_at', 'reviewed_at', 'document_url']
        extra_kwargs = {'document': {'write_only': True, 'required': False}}

    def get_document_url(self, obj):
        if obj.document and hasattr(obj.document, 'name') and obj.document.name:
            return self.context['request'].build_absolute_uri(reverse('protected_media', kwargs={'file_path': obj.document.name}))
        return None

    def create(self, validated_data):
        # Asigna el estudiante autenticado al crear la excusa
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)

class ExcuseCreateSerializer(serializers.ModelSerializer):
    """
    Serializador específico para que un estudiante cree una excusa.
    """
    class Meta:
        model = Excuse
        fields = ['session', 'reason', 'document']

    def validate_document(self, value):
        # Ensure that if a document is provided, it's an actual uploaded file.
        # This prevents accidental assignment of non-file paths.
        if value and not hasattr(value, 'file'):
            raise serializers.ValidationError("El documento debe ser un archivo subido.")
        return value

class ExcuseReviewSerializer(serializers.ModelSerializer):
    """
    Serializador para que un instructor revise (apruebe/rechace) una excusa.
    """
    class Meta:
        model = Excuse
        fields = ['status', 'review_comment']
        extra_kwargs = {
            'status': {'required': True},
        }

    def validate_status(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError("El estado solo puede ser 'approved' o 'rejected'.")
        return value