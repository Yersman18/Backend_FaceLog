# excuses/admin.py
from django.contrib import admin
from .models import Excuse

@admin.register(Excuse)
class ExcuseAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status', 'reviewed_by', 'created_at', 'reviewed_at']
    list_filter = ['status', 'session__ficha', 'created_at', 'reviewed_at']
    search_fields = ['student__username', 'student__first_name', 'student__last_name', 'session__ficha__numero_ficha', 'session__ficha__programa_formacion']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'reviewed_at']
    
    fieldsets = (
        ('Información de la Excusa', {
            'fields': ('student', 'session', 'reason', 'document')
        }),
        ('Estado de Revisión', {
            'fields': ('status', 'reviewed_by', 'review_comment', 'reviewed_at')
        }),
        ('Fechas', {
            'fields': ('created_at',)
        })
    )