# attendance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FichaViewSet,
    InstructorFichaListView,
    SessionViewSet,
    ManualAttendanceUpdateView,
    AttendanceLogViewSet,
    GlobalReportView,
    InstructorDashboardSummaryView, # Added import
    ApprenticeDashboardSummaryView, # Added import
    GlobalAttendancePDFReportView, # Added import
    ListAbsencesView,
    InstructorDailySessionsView, # Added import
    TodayAttendanceSessionListView,
    ApprenticeUpcomingSessionsView,
    FichaAttendanceReportView
)

# El router registra los ViewSets, que manejan las operaciones CRUD estandar
router = DefaultRouter()
router.register(r'fichas', FichaViewSet, basename='ficha')
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'attendance-logs', AttendanceLogViewSet, basename='attendance-log')

urlpatterns = [
    # Rutas generadas por el router
    path('', include(router.urls)),
    
    # Ruta específica para que un instructor vea su lista de fichas
    path('my-fichas/', InstructorFichaListView.as_view(), name='instructor-fichas'),

    # Ruta específica para que un instructor vea las sesiones programadas para el día
    path('instructor-daily-sessions/', InstructorDailySessionsView.as_view(), name='instructor-daily-sessions'),

    # Ruta específica para que un estudiante vea sus inasistencias
    path('absences/', ListAbsencesView.as_view(), name='student-absences'),

    # Ruta para el reporte global
    path('report/global/', GlobalReportView.as_view(), name='global-report'),
    
    # Ruta específica para la actualización manual de un registro de asistencia
    path('attendance-log/<int:pk>/update/', ManualAttendanceUpdateView.as_view(), name='manual-attendance-update'),

    # Ruta para el resumen del dashboard del instructor
    path('dashboard/instructor/summary/', InstructorDashboardSummaryView.as_view(), name='instructor-dashboard-summary'),

    # Ruta para el resumen del dashboard del aprendiz
    path('dashboard/apprentice/summary/', ApprenticeDashboardSummaryView.as_view(), name='apprentice-dashboard-summary'),

    # Ruta para las próximas sesiones del aprendiz
    path('dashboard/apprentice/upcoming-sessions/', ApprenticeUpcomingSessionsView.as_view(), name='apprentice-upcoming-sessions'),

    # Ruta para el reporte PDF global de asistencia
    path('report/global/pdf/', GlobalAttendancePDFReportView.as_view(), name='global-attendance-pdf-report'),
    path('today-sessions/', TodayAttendanceSessionListView.as_view(), name='today-sessions'),
    path('fichas/<int:ficha_id>/attendance-report/', FichaAttendanceReportView.as_view(), name='ficha-attendance-report'),
]