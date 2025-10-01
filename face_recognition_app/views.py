# face_recognition_app/views.py
from rest_framework import generics, views, permissions, status
from rest_framework.response import Response
from .models import FaceEncoding
from .serializers import FaceEncodingSerializer
from .services import get_face_encoding_from_image, recognize_faces_in_stream
from attendance.models import AttendanceSession
from attendance.permissions import IsInstructorOfFicha

class FacialRegistrationView(generics.CreateAPIView):
    """
    Vista para que un estudiante registre su rostro.
    Recibe una imagen (profile_image) y la procesa para crear una codificación facial.
    """
    queryset = FaceEncoding.objects.all()
    serializer_class = FaceEncodingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        image_file = request.data.get('profile_image')

        if not image_file:
            return Response({'error': 'No se proporcionó ninguna imagen.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generar codificación facial desde la imagen
        encoding = get_face_encoding_from_image(image_file)

        if encoding is None:
            return Response({'error': 'No se pudo detectar una única cara en la imagen. Intente con otra foto.'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear o actualizar el registro de FaceEncoding
        try:
            face_encoding_obj, created = FaceEncoding.objects.update_or_create(
                user=user,
                defaults={'profile_image': image_file}
            )
            face_encoding_obj.set_encoding_array(encoding)
            face_encoding_obj.save()
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(face_encoding_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class FacialRecognitionView(views.APIView):
    """
    Vista para el reconocimiento facial en tiempo real.
    Recibe una imagen y el ID de la sesión activa.
    """
    permission_classes = [permissions.IsAuthenticated, IsInstructorOfFicha]

    def post(self, request, *args, **kwargs):
        session_id = request.data.get('session_id')
        image_file = request.data.get('image')

        if not session_id or not image_file:
            return Response({'error': 'Se requiere session_id y una imagen.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = AttendanceSession.objects.get(id=session_id)
            # Verificar permisos del instructor sobre la ficha de la sesión
            self.check_object_permissions(request, session.ficha)
        except AttendanceSession.DoesNotExist:
            return Response({'error': 'La sesión de asistencia no existe.'}, status=status.HTTP_404_NOT_FOUND)

        if not session.is_active:
            return Response({'error': 'Esta sesión de asistencia no está activa para el reconocimiento facial.'}, status=status.HTTP_403_FORBIDDEN)

        # Llamar al servicio de reconocimiento
        result = recognize_faces_in_stream(image_file, session_id)

        if 'error' in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)