
import django_filters
from django.contrib.auth import get_user_model
from .models import Excuse

User = get_user_model()

class ExcuseFilter(django_filters.FilterSet):
    """
    Filtros para el modelo de Excusa.
    """
    student = django_filters.ModelChoiceFilter(queryset=User.objects.filter(role='student'), label='Aprendiz')
    date_from = django_filters.DateFilter(field_name='session__date', lookup_expr='gte', label='Desde (Fecha Sesión)')
    date_to = django_filters.DateFilter(field_name='session__date', lookup_expr='lte', label='Hasta (Fecha Sesión)')
    status = django_filters.ChoiceFilter(choices=Excuse.STATUS_CHOICES, label='Estado')

    class Meta:
        model = Excuse
        fields = ['student', 'date_from', 'date_to', 'status']
