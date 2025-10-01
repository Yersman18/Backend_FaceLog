# face_recognition_app/services.py
import face_recognition
import numpy as np
from io import BytesIO
from PIL import Image
from django.utils import timezone
from datetime import datetime
import logging
from django.conf import settings
from django.utils.timezone import make_aware
from django.core.cache import cache # Import cache

from attendance.models import Attendance, Ficha
from .models import FaceEncoding, FaceVerificationLog, FaceRecognitionSettings

logger = logging.getLogger(__name__)

def get_face_encoding_from_image(image_file):
    """
    Carga una imagen y devuelve la primera codificación facial encontrada.
    Devuelve None si no se encuentra ninguna cara o si hay más de una.
    """
    try:
        image = face_recognition.load_image_file(image_file)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 1:
            return encodings[0]
        logger.warning(f"Se encontraron {len(encodings)} caras en la imagen de perfil. Se esperaba 1.")
        return None
    except Exception as e:
        logger.error(f"Error al procesar la imagen para codificación: {e}")
        return None

def recognize_faces_in_stream(image_file, session_id):
    """
    Servicio principal para el reconocimiento facial en tiempo real.
    """
    logger.info(f"Iniciando reconocimiento facial para la sesión: {session_id}")
    try:
        settings = FaceRecognitionSettings.get_settings()
        logger.info(f"Usando umbral de confianza: {settings.confidence_threshold}")

        ficha = Ficha.objects.get(sessions__id=session_id)
        
        # --- Caching for known encodings ---
        cache_key = f"ficha_encodings_{ficha.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            known_encodings, known_student_ids = cached_data
            logger.info(f"Codificaciones cargadas desde caché para ficha {ficha.numero_ficha}.")
        else:
            students = ficha.students.all()
            logger.info(f"Ficha {ficha.numero_ficha} tiene {students.count()} estudiantes. Cargando desde DB.")

            known_encodings = []
            known_student_ids = []
            for student in students:
                if hasattr(student, 'face_encoding_data') and student.face_encoding_data.is_active:
                    encoding_array = student.face_encoding_data.get_encoding_array()
                    if encoding_array is not None and len(encoding_array) == 128:
                        known_encodings.append(encoding_array)
                        known_student_ids.append(student.id)
                    elif encoding_array is not None:
                        logger.warning(f"La codificación para el estudiante {student.id} tiene una longitud incorrecta: {len(encoding_array)}. Se omitirá.")
            
            if not known_encodings:
                logger.warning(f"No se encontraron codificaciones faciales activas para la ficha {ficha.numero_ficha}.")
                return {"error": "No hay rostros registrados o activos para esta ficha."}
            
            cache.set(cache_key, (known_encodings, known_student_ids), 3600) # Cache for 1 hour
            logger.info(f"Se cargaron {len(known_encodings)} codificaciones faciales conocidas y se guardaron en caché.")
        # --- End Caching ---

        stream_image = face_recognition.load_image_file(image_file)
        stream_locations = face_recognition.face_locations(stream_image, model=settings.face_detection_model)
        stream_encodings = face_recognition.face_encodings(stream_image, stream_locations)
        logger.info(f"Se detectaron {len(stream_encodings)} caras en la imagen recibida.")

        if not stream_encodings:
            return {"error": "No se detectó ningún rostro en la imagen."}

        recognized_students = []
        for i, stream_encoding in enumerate(stream_encodings):
            logger.info(f"Procesando cara {i+1} de {len(stream_encodings)}...")

            # Usar compare_faces para una lógica más robusta
            matches = face_recognition.compare_faces(known_encodings, stream_encoding, tolerance=settings.confidence_threshold)
            matched_indices = [i for i, match in enumerate(matches) if match]

            matched_student_id = None
            if len(matched_indices) == 1:
                # Coincidencia única y clara
                matched_student_id = known_student_ids[matched_indices[0]]
                distance = face_recognition.face_distance([known_encodings[matched_indices[0]]], stream_encoding)[0]
                logger.info(f"¡Coincidencia única encontrada! Estudiante ID: {matched_student_id} con distancia: {distance:.4f}")
            elif len(matched_indices) > 1:
                # Múltiples coincidencias, posible ambigüedad
                distances = face_recognition.face_distance([known_encodings[i] for i in matched_indices], stream_encoding)
                ambiguous_ids = [known_student_ids[i] for i in matched_indices]
                logger.warning(f"Ambigüedad detectada. Múltiples ({len(matched_indices)}) coincidencias por debajo del umbral para la cara {i+1}. IDs: {ambiguous_ids}. Distancias: {distances}")
            else:
                # Ninguna coincidencia por debajo del umbral
                min_distance = np.min(face_recognition.face_distance(known_encodings, stream_encoding))
                logger.warning(f"No hubo coincidencia para la cara {i+1}. Distancia mínima: {min_distance:.4f} (Umbral: {settings.confidence_threshold})")

            if matched_student_id:
                try:
                    attendance_record = Attendance.objects.get(session_id=session_id, student_id=matched_student_id)
                    logger.info(f"Registro de asistencia encontrado para el estudiante {matched_student_id}. Estado actual: {attendance_record.status}")
                    
                    if attendance_record.status == 'absent':
                        session = attendance_record.session
                        now = timezone.now()
                        
                        # Ensure session_start_datetime is timezone-aware
                        session_start_datetime = make_aware(datetime.combine(session.date, session.start_time))
                        grace_period_end = session_start_datetime + timezone.timedelta(minutes=session.permisividad)
                        
                        new_status = 'present' if now <= grace_period_end else 'late'
                        
                        attendance_record.status = new_status
                        attendance_record.check_in_time = now
                        attendance_record.verified_by_face = True
                        attendance_record.save()
                        logger.info(f"Asistencia actualizada para el estudiante {matched_student_id} a: {new_status}")
                        
                        recognized_students.append({
                            'id': attendance_record.student.id,
                            'full_name': attendance_record.student.get_full_name(),
                            'status': new_status
                        })
                    else:
                        logger.info(f"La asistencia para el estudiante {matched_student_id} ya fue registrada como '{attendance_record.status}'. No se actualiza.")

                except Attendance.DoesNotExist:
                    logger.error(f"Error: El estudiante reconocido con ID {matched_student_id} no tiene un registro de asistencia para esta sesión.")
                    continue

        return {"recognized_students": recognized_students}

    except Ficha.DoesNotExist:
        logger.error(f"Error crítico: La sesión de asistencia {session_id} no está asociada a ninguna ficha.")
        return {"error": "La sesión de asistencia no existe o no tiene una ficha asociada."}
    except Exception as e:
        logger.exception(f"Ocurrió una excepción no controlada durante el reconocimiento facial para la sesión {session_id}")
        return {"error": f"Ocurrió un error inesperado durante el reconocimiento: {e}"}