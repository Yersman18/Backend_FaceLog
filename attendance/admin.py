# attendance/admin.py
from django.contrib import admin
from .models import Ficha, AttendanceSession, Attendance

@admin.register(Ficha)
class FichaAdmin(admin.ModelAdmin):
    list_display = ['programa_formacion', 'numero_ficha', 'display_instructors', 'student_count', 'created_at']
    list_filter = ['instructors', 'created_at']
    search_fields = ['programa_formacion', 'numero_ficha', 'instructors__username', 'instructors__first_name', 'instructors__last_name']
    ordering = ['-created_at']
    filter_horizontal = ['students', 'instructors']

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Nº Estudiantes'

    def display_instructors(self, obj):
        return ", ".join([instructor.username for instructor in obj.instructors.all()])
    display_instructors.short_description = 'Instructores'

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['ficha', 'date', 'start_time', 'end_time', 'is_active', 'created_at']
    list_filter = ['ficha', 'date', 'is_active', 'created_at']
    search_fields = ['ficha__programa_formacion', 'ficha__numero_ficha', 'ficha__instructor__username']
    ordering = ['-date', '-start_time']
    date_hierarchy = 'date'

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['get_student_name', 'get_ficha', 'get_session_date', 'status', 'check_in_time', 'verified_by_face']
    list_filter = ['status', 'verified_by_face', 'session__ficha', 'session__date']
    search_fields = ['student__username', 'student__first_name', 'student__last_name', 'session__ficha__programa_formacion', 'session__ficha__numero_ficha']
    ordering = ['-session__date', '-session__start_time', 'student__last_name']
    date_hierarchy = 'session__date'

    def get_student_name(self, obj):
        return obj.student.username
    get_student_name.short_description = 'Estudiante'
    get_student_name.admin_order_field = 'student__last_name'

    def get_ficha(self, obj):
        return f"{obj.session.ficha.numero_ficha} - {obj.session.ficha.programa_formacion}"
    get_ficha.short_description = 'Ficha'
    get_ficha.admin_order_field = 'session__ficha__numero_ficha'

    def get_session_date(self, obj):
        return obj.session.date
    get_session_date.short_description = 'Fecha Sesión'
    get_session_date.admin_order_field = 'session__date'
