
import django_filters
from django.contrib.auth import get_user_model
from .models import Attendance, Ficha, AttendanceSession

User = get_user_model()

class AttendanceFilter(django_filters.FilterSet):
    """
    Filtros para el modelo de Asistencia.
    """
    # Filtro por rango de fechas para la sesión
    date_from = django_filters.DateFilter(field_name='session__date', lookup_expr='gte', label='Desde (Fecha)')
    date_to = django_filters.DateFilter(field_name='session__date', lookup_expr='lte', label='Hasta (Fecha)')
    
    # Filtro para una ficha específica
    ficha = django_filters.ModelChoiceFilter(queryset=Ficha.objects.all(), field_name='session__ficha', label='Ficha')

    class Meta:
        model = Attendance
        fields = ['date_from', 'date_to', 'ficha', 'status']

class FichaFilter(django_filters.FilterSet):
    """
    Filtros para el modelo de Ficha.
    """
    numero_ficha = django_filters.CharFilter(lookup_expr='icontains', label='Número de Ficha')
    programa_formacion = django_filters.CharFilter(lookup_expr='icontains', label='Programa de Formación')
    instructor = django_filters.ModelChoiceFilter(field_name='instructors', queryset=User.objects.filter(role='instructor'), label='Instructor')

    class Meta:
        model = Ficha
        fields = ['numero_ficha', 'programa_formacion', 'instructor']

class SessionFilter(django_filters.FilterSet):
    """
    Filtros para el modelo de Sesión de Asistencia.
    """
    date = django_filters.DateFilter(label='Fecha')
    ficha = django_filters.ModelChoiceFilter(queryset=Ficha.objects.all(), label='Ficha')
    is_active = django_filters.BooleanFilter(label='Activa')

    class Meta:
        model = AttendanceSession
        fields = ['date', 'ficha', 'is_active']
