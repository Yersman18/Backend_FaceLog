
import django_filters
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFilter(django_filters.FilterSet):
    """
    Filtros para el modelo de Usuario.
    """
    username = django_filters.CharFilter(lookup_expr='icontains', label='Username')
    email = django_filters.CharFilter(lookup_expr='icontains', label='Email')
    first_name = django_filters.CharFilter(lookup_expr='icontains', label='Nombre')
    last_name = django_filters.CharFilter(lookup_expr='icontains', label='Apellido')
    role = django_filters.ChoiceFilter(choices=User.ROLE_CHOICES, label='Rol')
    is_active = django_filters.BooleanFilter(label='Activo')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active']
