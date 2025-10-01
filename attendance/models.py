from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid

User = get_user_model()

class Ficha(models.Model):
    programa_formacion = models.CharField(max_length=100)
    numero_ficha = models.CharField(max_length=20, unique=True)
    jornada = models.CharField(max_length=50, blank=True, null=True)
    instructors = models.ManyToManyField(User, related_name='fichas', limit_choices_to={'role': 'instructor'})
    students = models.ManyToManyField(User, related_name='fichas_enrolled')
    created_at = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.numero_ficha} - {self.programa_formacion}"

class AttendanceSession(models.Model):
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='sessions', null=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    permisividad = models.IntegerField(default=0, help_text="Minutos de permisividad para llegar tarde")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['ficha', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.ficha.numero_ficha} - {self.date}"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Presente'),
        ('absent', 'Ausente'),
        ('late', 'Tardanza'),
        ('excused', 'Excusado'),
    ]
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    check_in_time = models.DateTimeField(null=True, blank=True)
    verified_by_face = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['session', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.session} - {self.status}"