# attendance/serializers.py
from rest_framework import serializers
from .models import Ficha, AttendanceSession, Attendance
from django.contrib.auth import get_user_model

User = get_user_model()

# Serializador simple para mostrar información de usuarios (estudiantes/instructores)
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'student_id']

class FichaSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Ficha. Permite ver y gestionar fichas.
    """
    instructors = SimpleUserSerializer(many=True, read_only=True)
    students = SimpleUserSerializer(many=True, read_only=True)
    
    instructor_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='instructor'), 
        write_only=True, 
        many=True, 
        source='instructors',
        required=False
    )
    student_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='student'), 
        write_only=True, 
        many=True, 
        source='students', 
        required=False
    )

    class Meta:
        model = Ficha
        fields = [
            'id', 'programa_formacion', 'numero_ficha', 'jornada', 'instructors', 'students',
            'instructor_ids', 'student_ids', 'created_at', 'fecha_inicio', 'fecha_fin'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        instructors_data = validated_data.pop('instructors', [])
        students_data = validated_data.pop('students', [])

        ficha = Ficha.objects.create(**validated_data)
        if instructors_data:
            ficha.instructors.set(instructors_data)
        if students_data:
            ficha.students.set(students_data)
        return ficha

    def update(self, instance, validated_data):
        # El pop previene que se intente asignar students directamente
        students_data = validated_data.pop('students', None)
        instructors_data = validated_data.pop('instructors', None)
        
        instance = super().update(instance, validated_data)
        
        # Si se proporcionaron student_ids, se actualiza la relación ManyToMany
        if students_data is not None:
            instance.students.set(students_data)
        if instructors_data is not None:
            instance.instructors.set(instructors_data)
        
        instance.refresh_from_db()
            
        return instance

class SimpleFichaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ficha
        fields = ['id', 'numero_ficha', 'programa_formacion']

class AttendanceSessionSerializer(serializers.ModelSerializer):
    """
    Serializador para las sesiones de asistencia.
    """
    ficha = SimpleFichaSerializer(read_only=True)
    ficha_id = serializers.PrimaryKeyRelatedField(
        queryset=Ficha.objects.all(),
        write_only=True,
        source='ficha',
        label='Ficha ID'
    )

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'date', 'start_time', 'end_time', 'is_active',
            'permisividad', 'created_at', 'ficha', 'ficha_id'
        ]
        read_only_fields = ['id', 'created_at', 'ficha']

class AttendanceLogSerializer(serializers.ModelSerializer):
    """
    Serializador para los registros de asistencia individuales.
    """
    student = SimpleUserSerializer(read_only=True)
    session = AttendanceSessionSerializer(read_only=True) # Use nested serializer

    class Meta:
        model = Attendance
        fields = ['id', 'session', 'student', 'status', 'check_in_time', 'verified_by_face']
        read_only_fields = ['id', 'session', 'student', 'check_in_time', 'verified_by_face']

class AttendanceLogUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para la edición manual de un registro de asistencia por parte de un instructor.
    """
    class Meta:
        model = Attendance
        fields = ['status'] # Solo se puede cambiar el estado

class SimpleAttendanceSessionSerializer(serializers.ModelSerializer):
    ficha = SimpleFichaSerializer(read_only=True)
    class Meta:
        model = AttendanceSession
        fields = ['id', 'date', 'start_time', 'end_time', 'ficha']