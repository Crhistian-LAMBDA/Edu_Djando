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
