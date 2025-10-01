# attendance/permissions.py
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a los administradores crear/editar/eliminar.
    Otros usuarios (autenticados) pueden ver (GET, HEAD, OPTIONS).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.role == 'admin'

class IsInstructorOfFicha(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es el instructor de la ficha asociada al objeto.
    """
    def has_object_permission(self, request, view, obj):
        from .models import Ficha, AttendanceSession, Attendance

        ficha = None
        if isinstance(obj, Ficha):
            ficha = obj
        elif isinstance(obj, AttendanceSession):
            ficha = obj.ficha
        elif isinstance(obj, Attendance):
            ficha = obj.session.ficha
        
        if ficha:
            return ficha.instructors.filter(id=request.user.id).exists()
            
        return False

class IsStudentInFicha(permissions.BasePermission):
    """
    Permiso para verificar si el usuario es un estudiante inscrito en la ficha.
    """
    def has_object_permission(self, request, view, obj):
        ficha = obj.ficha if hasattr(obj, 'ficha') else obj
        return ficha.students.filter(id=request.user.id).exists()

class IsInstructor(permissions.BasePermission):
    """
    Permiso personalizado para permitir el acceso solo a usuarios con rol 'instructor'.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'instructor'