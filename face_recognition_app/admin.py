from django.contrib import admin
from .models import FaceEncoding, FaceVerificationLog, FaceRecognitionSettings
from .services import get_face_encoding_from_image
from django.contrib import messages

@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('encoding_data', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_image', 'is_active')
        }),
        ('Datos de Codificación (Solo Lectura)', {
            'fields': ('encoding_data',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if 'profile_image' in form.changed_data:
            new_image = form.cleaned_data.get('profile_image')
            if new_image:
                encoding = get_face_encoding_from_image(new_image)
                if encoding is not None:
                    try:
                        obj.set_encoding_array(encoding)
                        messages.success(request, "La codificación facial se ha actualizado correctamente a partir de la nueva imagen.")
                    except ValueError as e:
                        messages.error(request, f"No se pudo actualizar la codificación facial: {e}")
                else:
                    messages.warning(request, "No se pudo detectar una cara en la nueva imagen. La codificación no se ha actualizado.")
            else:
                obj.encoding_data = "[]"
                messages.info(request, "Se ha eliminado la imagen de perfil y la codificación facial.")

        super().save_model(request, obj, form, change)

@admin.register(FaceVerificationLog)
class FaceVerificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'status', 'confidence_score', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'session__ficha__numero_ficha')
    readonly_fields = ('created_at',)

@admin.register(FaceRecognitionSettings)
class FaceRecognitionSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'confidence_threshold', 'max_verification_attempts', 'face_detection_model', 'is_active')
    fieldsets = (
        ('Configuración General', {
            'fields': ('is_active', 'enable_logging')
        }),
        ('Parámetros del Modelo', {
            'fields': ('confidence_threshold', 'max_verification_attempts', 'face_detection_model')
        }),
    )

    def has_add_permission(self, request):
        return not FaceRecognitionSettings.objects.exists()
