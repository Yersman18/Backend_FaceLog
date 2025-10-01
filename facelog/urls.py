# facelog/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views # Import views from the current app
from excuses.views import protected_media_view

# Agrupar las URLs de la API bajo un solo prefijo para versionado y claridad
api_v1_patterns = [
    path('auth/', include('authentication.urls')),
    path('attendance/', include('attendance.urls')),
    path('excuses/', include('excuses.urls')),
    path('face/', include('face_recognition_app.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),
    path('test-facelog/', views.test_view, name='test-facelog'), # New test URL
    re_path(r'^protected_media/(?P<file_path>.*)', protected_media_view, name='protected_media'),
]

# Servir archivos multimedia en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)