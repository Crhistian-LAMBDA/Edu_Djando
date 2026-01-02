from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_welcome_email(user_email, username, first_name, password):
    """
    Tarea asíncrona para enviar correo de bienvenida a nuevos usuarios con contraseña
    """
    subject = '¡Bienvenido al Sistema de Gestión Escolar!'
    
    message = f"""
    Hola {first_name},

    ¡Bienvenido al Sistema de Gestión Escolar!

    Tu cuenta ha sido creada exitosamente.

    Credenciales de acceso:
    Usuario: {username}
    Contraseña: {password}

    Ya puedes acceder al sistema con tus credenciales.

    Saludos,
    El equipo de Colegio Django
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                <div style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #4CAF50; text-align: center;">¡Bienvenido al Sistema de Gestión Escolar!</h2>
                    
                    <p>Hola <strong>{first_name}</strong>,</p>
                    
                    <p>Tu cuenta ha sido creada exitosamente.</p>
                    
                    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Usuario:</strong> {username}</p>
                        <p style="margin: 5px 0;"><strong>Contraseña:</strong> {password}</p>
                    </div>
                    
                    <p>Ya puedes acceder al sistema con tus credenciales.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #777; font-size: 12px; text-align: center;">
                        Este es un correo automático, por favor no responder.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return f'Email enviado exitosamente a {user_email}'
    except Exception as e:
        return f'Error al enviar email: {str(e)}'


@shared_task
def send_password_recovery_email(user_email, first_name, token):
    """
    Tarea asíncrona para enviar correo de recuperación de contraseña
    """
    enlace = f"http://localhost:3000/reset-password?token={token}"
    subject = 'Recuperación de Contraseña - Colegio Django'
    
    message = f"""
Hola {first_name},

Has solicitado recuperar tu contraseña en el sistema de Colegio Django.

Haz clic en el siguiente enlace para establecer una nueva contraseña:
{enlace}

Este enlace expira en 1 hora.

Si no solicitaste este cambio, ignora este correo.

Saludos,
Sistema de Gestión Educativa - Colegio Django
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                <div style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF9800; text-align: center;">Recuperación de Contraseña</h2>
                    
                    <p>Hola <strong>{first_name}</strong>,</p>
                    
                    <p>Has solicitado recuperar tu contraseña en el sistema de Colegio Django.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{enlace}" style="background-color: #FF9800; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Restablecer Contraseña
                        </a>
                    </div>
                    
                    <p style="color: #777; font-size: 14px;">
                        Este enlace expira en <strong>1 hora</strong>.
                    </p>
                    
                    <p style="color: #777; font-size: 14px;">
                        Si no solicitaste este cambio, ignora este correo.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #777; font-size: 12px; text-align: center;">
                        Este es un correo automático, por favor no responder.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return f'Email de recuperación enviado exitosamente a {user_email}'
    except Exception as e:
        return f'Error al enviar email de recuperación: {str(e)}'


@shared_task
def send_asignatura_assignment_email(docente_email, docente_nombre, asignatura_nombre, asignatura_codigo, periodo_nombre, descripcion):
    """
    Tarea asíncrona para notificar al docente cuando se le asigna una asignatura
    """
    subject = f'Nueva Asignatura Asignada - {asignatura_codigo}'
    
    message = f"""
Hola {docente_nombre},

Le informamos que ha sido asignado como docente responsable de una nueva asignatura.

Detalles de la Asignatura:
Nombre: {asignatura_nombre}
Código: {asignatura_codigo}
Período: {periodo_nombre}
Descripción: {descripcion if descripcion else 'Sin descripción'}

Ya puede acceder al sistema para ver más detalles.

Saludos,
Sistema de Gestión Educativa - Colegio Django
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                <div style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #2196F3; text-align: center;">Nueva Asignatura Asignada</h2>
                    
                    <p>Hola <strong>{docente_nombre}</strong>,</p>
                    
                    <p>Le informamos que ha sido asignado como docente responsable de una nueva asignatura.</p>
                    
                    <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #2196F3; margin: 20px 0;">
                        <p style="margin: 10px 0;"><strong>Nombre:</strong> {asignatura_nombre}</p>
                        <p style="margin: 10px 0;"><strong>Código:</strong> {asignatura_codigo}</p>
                        <p style="margin: 10px 0;"><strong>Período Académico:</strong> {periodo_nombre}</p>
                        <p style="margin: 10px 0;"><strong>Descripción:</strong> {descripcion if descripcion else 'Sin descripción'}</p>
                    </div>
                    
                    <p>Ya puede acceder al sistema para ver más detalles y gestionar la asignatura.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #777; font-size: 12px; text-align: center;">
                        Este es un correo automático, por favor no responder.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[docente_email],
            html_message=html_message,
            fail_silently=False,
        )
        return f'Email de asignación enviado exitosamente a {docente_email}'
    except Exception as e:
        return f'Error al enviar email de asignación: {str(e)}'


@shared_task
def send_approval_pending_email(user_email, first_name):
    """
    Enviar correo cuando un usuario se registra indicando que está pendiente de aprobación
    """
    subject = 'Tu solicitud de registro está pendiente de aprobación'
    
    message = f"""
    Hola {first_name},

    Gracias por registrarte en el Sistema de Gestión Escolar.

    Tu cuenta ha sido creada exitosamente, pero está pendiente de aprobación por un administrador.

    Por favor espera mientras verifican tu información y asignan los roles correspondientes.

    Una vez que tu cuenta sea activada, recibirás un nuevo correo con tu acceso aprobado.

    Saludos,
    El equipo de Colegio Django
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                <div style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #FF9800; text-align: center;">Solicitud Pendiente de Aprobación</h2>
                    
                    <p>Hola <strong>{first_name}</strong>,</p>
                    
                    <p>Gracias por registrarte en el <strong>Sistema de Gestión Escolar</strong>.</p>
                    
                    <p>Tu cuenta ha sido creada exitosamente, pero está pendiente de aprobación por un administrador.</p>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #FF9800; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⏳ Estado:</strong> Pendiente de aprobación</p>
                        <p style="margin: 10px 0 0 0; font-size: 14px;">Por favor espera mientras verifican tu información y asignan los roles correspondientes.</p>
                    </div>
                    
                    <p>Una vez que tu cuenta sea activada, recibirás un nuevo correo con tu acceso aprobado.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #777; font-size: 12px; text-align: center;">
                        El equipo de Colegio Django
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return f'Email de solicitud pendiente enviado a {user_email}'
    except Exception as e:
        return f'Error al enviar email: {str(e)}'


@shared_task
def send_approval_welcome_email(user_email, first_name, roles):
    """
    Enviar correo de bienvenida cuando Admin aprueba el usuario
    """
    roles_str = ', '.join(roles)
    subject = '¡Tu cuenta ha sido aprobada! Acceso al Sistema de Gestión Escolar'
    
    message = f"""
    Hola {first_name},

    ¡Buenas noticias! Tu cuenta ha sido aprobada y activada.

    Roles asignados: {roles_str}

    Ya puedes acceder al Sistema de Gestión Escolar con tu correo y contraseña.

    Enlace de acceso: {settings.FRONTEND_URL}/login

    Saludos,
    El equipo de Colegio Django
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
                <div style="background-color: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #4CAF50; text-align: center;">¡Cuenta Aprobada!</h2>
                    
                    <p>Hola <strong>{first_name}</strong>,</p>
                    
                    <p>¡Buenas noticias! Tu cuenta ha sido aprobada y activada.</p>
                    
                    <div style="background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>✓ Estado:</strong> Activo</p>
                        <p style="margin: 5px 0;"><strong>Roles asignados:</strong> {roles_str}</p>
                    </div>
                    
                    <p>Ya puedes acceder al Sistema de Gestión Escolar con tu correo y contraseña.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/login" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Acceder al Sistema
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #777; font-size: 12px; text-align: center;">
                        El equipo de Colegio Django
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return f'Email de aprobación enviado a {user_email}'
    except Exception as e:
        return f'Error al enviar email: {str(e)}'