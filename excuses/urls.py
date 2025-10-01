from django.urls import path
from .views import ExcuseViewSet

urlpatterns = [
    path('', ExcuseViewSet.as_view({'post': 'create', 'get': 'list'}), name='excuse-list'),
    path('<int:pk>/', ExcuseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='excuse-detail'),
]