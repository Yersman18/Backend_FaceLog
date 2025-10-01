from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import Excuse
from .serializers import ExcuseSerializer, ExcuseCreateSerializer, ExcuseReviewSerializer
from attendance.permissions import IsInstructorOfFicha
from attendance.models import Attendance
from rest_framework.exceptions import ValidationError
from .filters import ExcuseFilter # Import the new filter
import os
from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Excuse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_media_view(request, file_path):
    """
    A view to serve protected media files.
    It checks if the user has the right to access the file.
    """
    # Prevent directory traversal attacks
    if '..' in file_path:
        raise Http404

    # Get the excuse associated with the document
    try:
        # The file_path in the URL will be like 'excuses/2025/09/file.pdf'
        excuse = Excuse.objects.get(document=file_path)
    except Excuse.DoesNotExist:
        raise Http404

    user = request.user
    # Check permissions
    if user.role == 'student' and excuse.student != user:
        raise Http404 # Or PermissionDenied

    if user.role == 'instructor' and not excuse.session.ficha.instructors.filter(id=user.id).exists():
        raise Http404 # Or PermissionDenied

    # Construct the full file path
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)

    if not os.path.exists(full_path):
        raise Http404

    return FileResponse(open(full_path, 'rb'))


class ExcuseViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de Excusas.
    - Estudiantes: Pueden crear excusas para sus sesiones y ver las suyas.
    - Instructores: Pueden ver las excusas de sus fichas y aprobarlas/rechazarlas.
    - Administradores: Pueden ver todas las excusas.
    """
    queryset = Excuse.objects.all().select_related('student', 'session__ficha', 'reviewed_by')
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = ExcuseFilter # Add filterset_class here

    def get_serializer_class(self):
        if self.action == 'create':
            return ExcuseCreateSerializer
        # Para PATCH, un instructor está revisando
        if self.action == 'partial_update':
            return ExcuseReviewSerializer
        return ExcuseSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset() # Get the base queryset
        if user.role == 'student':
            queryset = queryset.filter(student=user)
        if user.role == 'instructor':
            queryset = queryset.filter(session__ficha__instructors=user)
        if user.role == 'admin':
            pass # Admins see all, no additional filter needed for them
        return queryset

    def perform_create(self, serializer):
        session = serializer.validated_data.get('session')
        user = self.request.user

        # Validar que el estudiante solo pueda crear excusas para sesiones en las que está inscrito.
        if not session.ficha.students.filter(id=user.id).exists():
            raise permissions.PermissionDenied("No puede crear una excusa para una sesión a la que no pertenece.")

        # Validar que el estudiante solo pueda presentar excusas para sesiones en las que faltó.
        try:
            attendance_record = Attendance.objects.get(student=user, session=session)
            if attendance_record.status != 'absent':
                raise ValidationError("Solo puede presentar excusas para las sesiones a las que ha faltado.")
        except Attendance.DoesNotExist:
            raise ValidationError("No se encontró un registro de asistencia para esta sesión.")

        # Validar que no exista ya una excusa para esa sesión
        if Excuse.objects.filter(student=user, session=session).exists():
            raise ValidationError("Ya existe una excusa para esta sesión.")
            
        serializer.save(student=user)

    def perform_update(self, serializer):
        excuse = self.get_object()
        user = self.request.user

        if user.role != 'instructor':
            raise permissions.PermissionDenied("Solo los instructores pueden revisar excusas.")

        # Usar el permiso para verificar que el instructor es el de la ficha correcta
        permission = IsInstructorOfFicha()
        if not permission.has_object_permission(self.request, self, excuse.session.ficha):
             raise permissions.PermissionDenied("No tiene permiso para revisar excusas de esta ficha.")

        if excuse.status != 'pending':
            raise ValidationError("Esta excusa ya ha sido revisada.")

        # El modelo ya se encarga de actualizar la asistencia si se aprueba
        serializer.save(reviewed_by=user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # After updating, serialize with the default serializer
        response_serializer = ExcuseSerializer(instance, context={'request': request})
        return Response(response_serializer.data)