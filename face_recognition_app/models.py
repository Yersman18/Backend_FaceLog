# face_recognition_app/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)
User = settings.AUTH_USER_MODEL

class FaceEncoding(models.Model):
    """
    Modelo para almacenar las codificaciones faciales de los usuarios.
    Separado del modelo User para mayor flexibilidad y posibles futuras extensiones.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='face_encoding_data'
    )
    encoding_data = models.TextField(
        help_text="Codificación facial almacenada como JSON string"
    )
    profile_image = models.ImageField(
        upload_to='face_profiles/',
        null=True,
        blank=True,
        help_text="Imagen utilizada para generar la codificación facial"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si esta codificación facial está activa"
    )
    
    class Meta:
        verbose_name = "Codificación Facial"
        verbose_name_plural = "Codificaciones Faciales"
    
    def __str__(self):
        return f"Face encoding for {self.user.username}"
    
    def get_encoding_array(self):
        """Convierte el JSON string de vuelta a lista de Python"""
        try:
            encoding = json.loads(self.encoding_data)
            logger.info(f"Loaded encoding for user {self.user.username} with length {len(encoding) if encoding else 0}")
            return encoding
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Could not decode encoding for user {self.user.username}")
            return None
    
    def set_encoding_array(self, encoding_array):
        """Convierte la lista de encoding a JSON string y valida su integridad."""
        if encoding_array is None or len(encoding_array) != 128:
            logger.error(f"Intento de guardar una codificación inválida para el usuario {self.user.username}. Longitud: {len(encoding_array) if encoding_array is not None else 'None'}")
            raise ValueError("La codificación facial proporcionada es inválida o está vacía.")

        try:
            self.encoding_data = json.dumps(encoding_array.tolist() if hasattr(encoding_array, 'tolist') else encoding_array)
        except (TypeError, AttributeError) as e:
            logger.error(f"Error al serializar la codificación para el usuario {self.user.username}: {e}")
            raise ValueError("No se pudo serializar la codificación facial.")

class FaceVerificationLog(models.Model):
    """
    Modelo para llevar un registro de todos los intentos de verificación facial.
    Útil para auditoría y análisis de seguridad.
    """
    STATUS_CHOICES = [
        ('success', 'Exitoso'),
        ('failed', 'Fallido'),
        ('no_face_detected', 'No se detectó rostro'),
        ('no_registered_face', 'Sin rostro registrado'),
        ('error', 'Error del sistema'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='face_verification_logs'
    )
    session = models.ForeignKey(
        'attendance.AttendanceSession',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Sesión de asistencia asociada (si aplica)"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='failed'
    )
    confidence_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Puntuación de confianza de la verificación (0-1)"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="Dirección IP desde donde se realizó la verificación"
    )
    user_agent = models.TextField(
        null=True, 
        blank=True,
        help_text="User agent del navegador/dispositivo"
    )
    error_message = models.TextField(
        null=True, 
        blank=True,
        help_text="Mensaje de error si la verificación falló"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Verificación Facial"
        verbose_name_plural = "Logs de Verificación Facial"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class FaceRecognitionSettings(models.Model):
    """
    Configuraciones globales para el sistema de reconocimiento facial.
    """
    confidence_threshold = models.FloatField(
        default=0.55,
        help_text="Umbral de confianza para considerar una coincidencia válida (menor valor = más estricto)"
    )
    max_verification_attempts = models.IntegerField(
        default=3,
        help_text="Número máximo de intentos de verificación por sesión"
    )
    face_detection_model = models.CharField(
        max_length=50,
        default='hog',
        choices=[
            ('hog', 'HOG (CPU)'),
            ('cnn', 'CNN (GPU)'),
        ],
        help_text="Modelo a usar para detección facial"
    )
    enable_logging = models.BooleanField(
        default=True,
        help_text="Habilitar logging de verificaciones faciales"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Sistema de reconocimiento facial activo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Reconocimiento Facial"
        verbose_name_plural = "Configuraciones de Reconocimiento Facial"
    
    def __str__(self):
        return f"Face Recognition Settings - Active: {self.is_active}"
    
    @classmethod
    def get_settings(cls):
        """Obtiene la configuración actual o crea una por defecto"""
        settings, created = cls.objects.get_or_create(
            is_active=True,
            defaults={
                'confidence_threshold': 0.55,
                'max_verification_attempts': 3,
                'face_detection_model': 'hog',
                'enable_logging': True,
            }
        )
        return settings