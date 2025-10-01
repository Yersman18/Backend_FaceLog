from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser
from .serializers import UserSerializer, RegisterStudentSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, ChangePasswordSerializer, InstructorSerializer
from .models import PasswordResetToken
from attendance.permissions import IsAdminOrReadOnly # Reusing this permission
from django.utils import timezone
from datetime import timedelta
from .filters import UserFilter # Import the new filter
from rest_framework import serializers

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el token JWT para incluir el rol y el nombre del usuario.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Añadir campos personalizados al payload del token
        token['role'] = user.role
        token['full_name'] = user.get_full_name()
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)

        # This line is not strictly necessary because of raise_exception=True, but kept for clarity
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterStudentView(generics.CreateAPIView):
    """
    Vista para que un nuevo aprendiz se registre.
    No requiere autenticación.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny] # Cualquiera puede registrarse
    serializer_class = RegisterStudentSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vista para que un usuario vea o actualice su perfil.
    Requiere autenticación.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Devuelve el perfil del usuario que hace la petición
        return self.request.user

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            # Eliminar tokens viejos para este usuario
            PasswordResetToken.objects.filter(user=user).delete()
            token = PasswordResetToken.objects.create(user=user)
            # En una aplicación real, aquí se enviaría un email al usuario con el token
            # Por ahora, devolvemos el token en la respuesta para facilitar las pruebas
            return Response({'token': str(token.token)}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "No existe un usuario con ese correo electrónico."}, status=status.HTTP_404_NOT_FOUND)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            token = PasswordResetToken.objects.get(token=data['token'])
            if token.created_at < timezone.now() - timedelta(hours=1):
                token.delete()
                return Response({"error": "El token ha expirado."}, status=status.HTTP_400_BAD_REQUEST)
            
            user = token.user
            user.set_password(data['password'])
            user.save()
            token.delete()
            return Response({"success": "Contraseña restablecida exitosamente."}, status=status.HTTP_200_OK)
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Token inválido."}, status=status.HTTP_404_NOT_FOUND)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para que los Administradores gestionen usuarios (CRUD completo).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] # Allow authenticated users to list users
    filterset_class = UserFilter # Add filterset_class here

    def get_queryset(self):
        try:
            # Apply default queryset filtering based on role if needed, then apply filters
            queryset = super().get_queryset()
            user = self.request.user

            if user.is_authenticated and user.role == 'instructor':
                # Instructors can only see students in their assigned fichas
                instructor_fichas = user.fichas.all()
                student_ids_in_fichas = []
                for ficha in instructor_fichas:
                    student_ids_in_fichas.extend(ficha.students.values_list('id', flat=True))
                queryset = queryset.filter(id__in=student_ids_in_fichas, role='student').distinct()
            elif user.is_authenticated and user.role == 'student':
                # Students can only see their own profile
                queryset = queryset.filter(id=user.id)
            elif user.is_authenticated and user.role == 'admin':
                # Admins see all users, no additional filter needed for them
                pass
            else:
                # For unauthenticated users or other roles, return an empty queryset
                queryset = User.objects.none()

            return queryset
        except Exception as e:
            print(f"Error in UserViewSet get_queryset: {e}")
            traceback.print_exc()
            raise e

    def get_serializer_class(self):
        if self.action == 'create':
            # When creating a user from admin, allow setting role
            class AdminUserCreateSerializer(UserSerializer):
                role = serializers.CharField() # Make role writable
                class Meta(UserSerializer.Meta):
                    fields = UserSerializer.Meta.fields + ['password']
                    extra_kwargs = {'password': {'write_only': True}}

                def create(self, validated_data):
                    try:
                        # Pop role and student_id before calling create_user
                        role = validated_data.pop('role')
                        student_id = validated_data.pop('student_id', None)

                        user = User.objects.create_user(
                            username=validated_data['username'],
                            email=validated_data['email'],
                            password=validated_data['password'],
                            first_name=validated_data.get('first_name', ''),
                            last_name=validated_data.get('last_name', ''),
                            role=role,  # Pass role here
                            student_id=student_id # Pass student_id here
                        )
                        return user
                    except Exception as e:
                        print(f"Error creating user: {e}")
                        traceback.print_exc()
                        raise e
            return AdminUserCreateSerializer
        return UserSerializer

class InstructorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para que los Administradores gestionen instructores (CRUD completo).
    """
    queryset = User.objects.filter(role='instructor')
    serializer_class = InstructorSerializer
    permission_classes = [permissions.IsAdminUser] # Solo administradores pueden gestionar instructores

    def get_queryset(self):
        return User.objects.filter(role='instructor')

    def perform_create(self, serializer):
        # Ensure the role is set to 'instructor' when creating via this viewset
        serializer.save(role='instructor')

    def perform_update(self, serializer):
        # Ensure the role remains 'instructor' when updating via this viewset
        serializer.save(role='instructor')