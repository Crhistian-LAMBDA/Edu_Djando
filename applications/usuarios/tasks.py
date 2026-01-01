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
