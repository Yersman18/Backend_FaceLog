# excuses/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from attendance.models import AttendanceSession, Attendance

User = settings.AUTH_USER_MODEL

class Excuse(models.Model):
    """
    Modelo para manejar las excusas de los estudiantes.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_excuses',
        limit_choices_to={'role': 'student'}
    )
    
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='excuses'
    )
    
    reason = models.TextField(help_text="Descripción detallada de la excusa")
    document = models.FileField(upload_to='excuses/%Y/%m/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_excuses',
        limit_choices_to={'role': 'instructor'}
    )
    
    review_comment = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Excusa"
        verbose_name_plural = "Excusas"
        unique_together = ['student', 'session']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.session} - {self.get_status_display()}"

    def clean(self):
        if self.student and self.session:
            if not self.session.ficha.students.filter(id=self.student.id).exists():
                raise ValidationError("El estudiante no está inscrito en la ficha de esta sesión.")

    def save(self, *args, **kwargs):
        # Marcar la fecha de revisión si el estado cambia a aprobado o rechazado
        if self.pk is not None:
            orig = Excuse.objects.get(pk=self.pk)
            if orig.status == 'pending' and self.status in ['approved', 'rejected']:
                self.reviewed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Si se aprueba la excusa, actualizar la asistencia correspondiente
        if self.status == 'approved':
            attendance, created = Attendance.objects.get_or_create(
                session=self.session,
                student=self.student,
                defaults={'status': 'excused'}
            )
            if not created and attendance.status != 'excused':
                attendance.status = 'excused'
                attendance.save()
