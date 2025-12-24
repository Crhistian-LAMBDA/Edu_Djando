# EduPro 360 – Django + DRF + JWT + Celery

## Requisitos

- Python 3.13
- PostgreSQL (con `psql` o pgAdmin)
- Redis (WSL/Docker/Memurai en Windows)
- VS Code con extensiones Python y Pylance

## Preparación

```powershell
# En la carpeta del proyecto
python -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Base de datos

```powershell
# Crear BD (ajusta usuario/puerto si aplica)
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE educar;"
```

Configura credenciales en `edu/settings.py`.

## Migraciones

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Redis + Celery

- Redis: inicia el servicio (WSL/Docker/Memurai).

```powershell
# Verificar redis
redis-cli ping
# Worker Celery en Windows
celery -A edu worker -l info --pool=solo
```

## Servidor

```powershell
python manage.py runserver
```

## Gmail App Password

1. Cuenta Google → Seguridad → Verificación en dos pasos (activar).
2. Contraseñas de aplicaciones → generar para "Correo" y "Windows".
3. Pon el código en `EMAIL_HOST_PASSWORD` y tu email en `EMAIL_HOST_USER`.

## Endpoints

- POST `/api/usuarios/registro/` – crea usuario y envía email.
- POST `/api/usuarios/login/` – devuelve `access` y `refresh`.
- GET `/api/usuarios/me/` – perfil del usuario autenticado.
- Swagger: GET `/api/docs/`.

## Generar Guía PDF

```powershell
python scripts/run_generar_pdf.py
```

El PDF se guarda en `docs/Guia_Proyecto_EduPro360.pdf`.
