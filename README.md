# Sistema de Gestión Educativa - Backend (Django)

Sistema integral de gestión académica desarrollado con Django REST Framework, diseñado para administrar usuarios, instituciones educativas, estudiantes, docentes y procesos académicos.

## 🚀 Características

### Gestión de Usuarios (HU-01 y HU-02)

- ✅ Registro de usuarios con validación de campos (nombre, apellido, email, número de documento)
- ✅ Login con email y contraseña (HU-02)
- ✅ Autenticación JWT con tokens de acceso (1 hora) y refresh (7 días)
- ✅ Renovación automática de tokens mediante `/api/token/refresh/`
- ✅ Sistema de roles (Administrador, Docente, Estudiante)
- ✅ Gestión de perfiles con foto de avatar
- ✅ Cambio de contraseña seguro con validación
- ✅ Control de usuarios activos/inactivos

### Gestión Académica

- Instituciones educativas
- Sedes y sucursales
- Grados académicos
- Asignaturas y currículum
- Asignación docente-asignatura
- Asignación estudiante-grado
- Gestión de períodos académicos

### Seguridad

- Autenticación basada en JWT (Simple JWT)
- Control de permisos por rol
- Validación de contraseñas con requisitos mínimos
- CORS configurado para frontend
- Protección contra acceso no autorizado (401, 403)

### Documentación API

- Swagger UI integrado en `/api/docs/`
- Redoc disponible en `/api/redoc/`
- Esquema OpenAPI completo

## 📋 Requisitos

- Python 3.10+
- PostgreSQL 12+
- Redis (opcional, para Celery)
- Git

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Crhistian-LAMBDA/Edu_Djando.git
cd Edu_Djando
```

### 2. Crear y activar entorno virtual

**Windows:**

```powershell
python -m venv env
.\env\Scripts\activate
```

**Linux/Mac:**

```bash
python3 -m venv env
source env/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Crear base de datos PostgreSQL:

```sql
CREATE DATABASE colegio_db;
CREATE USER colegio_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE colegio_db TO colegio_user;
```

### 5. Configurar variables de entorno

Editar `edu/settings.py` y ajustar:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'colegio_db',
        'USER': 'colegio_user',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 6. Aplicar migraciones

```bash
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Ejecutar servidor

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## 🧪 Tests

Ejecutar todos los tests:

```bash
python manage.py test
```

Ejecutar tests con verbosidad:

```bash
python manage.py test applications.usuarios -v 2
```

Tests implementados:

- ✅ Registro de usuarios
- ✅ Login con email y password
- ✅ Permisos por rol (403 cuando no autorizado)
- ✅ Validación de usuarios activos
- ✅ Asignaciones académicas

## 📚 API Endpoints

### Autenticación

| Método | Endpoint                             | Descripción                           |
| ------ | ------------------------------------ | ------------------------------------- |
| POST   | `/api/usuarios/registro/`            | Registrar nuevo usuario               |
| POST   | `/api/usuarios/login/`               | Iniciar sesión (devuelve tokens JWT)  |
| POST   | `/api/token/refresh/`                | Renovar token de acceso               |
| GET    | `/api/usuarios/me/`                  | Obtener datos del usuario autenticado |
| POST   | `/api/usuarios/me/cambiar_password/` | Cambiar contraseña                    |

### Gestión de Usuarios (requiere autenticación)

| Método | Endpoint              | Descripción            | Rol requerido         |
| ------ | --------------------- | ---------------------- | --------------------- |
| GET    | `/api/usuarios/`      | Listar usuarios        | Administrador/Docente |
| GET    | `/api/usuarios/{id}/` | Obtener usuario por ID | Administrador         |
| PUT    | `/api/usuarios/{id}/` | Actualizar usuario     | Administrador         |
| DELETE | `/api/usuarios/{id}/` | Eliminar usuario       | Administrador         |

### Gestión Académica

| Método   | Endpoint                      | Descripción                                  |
| -------- | ----------------------------- | -------------------------------------------- |
| GET/POST | `/api/instituciones/`         | Listar/Crear instituciones                   |
| GET/POST | `/api/sedes/`                 | Listar/Crear sedes                           |
| GET/POST | `/api/grados/`                | Listar/Crear grados                          |
| GET/POST | `/api/asignaturas/`           | Listar/Crear asignaturas                     |
| GET/POST | `/api/asignacion-docente/`    | Listar/Crear asignaciones docente-asignatura |
| GET/POST | `/api/asignacion-estudiante/` | Listar/Crear asignaciones estudiante-grado   |

### Documentación

- **Swagger UI:** http://localhost:8000/api/docs/
- **Redoc:** http://localhost:8000/api/redoc/

## 🗂️ Estructura del Proyecto

```
edu/
├── applications/          # Aplicaciones Django
│   └── usuarios/         # Gestión de usuarios
│       ├── api/          # Vistas y serializadores API
│       ├── migrations/   # Migraciones de base de datos
│       ├── models.py     # Modelos de datos
│       └── tests.py      # Tests unitarios
├── docs/                 # Documentación del proyecto
│   └── Guia_Replicacion_Proyecto.md
├── edu/                  # Configuración principal
│   ├── settings.py       # Configuración Django
│   ├── urls.py          # URLs principales
│   └── celery.py        # Configuración Celery (opcional)
├── scripts/             # Scripts auxiliares
├── manage.py            # CLI de Django
└── requirements.txt     # Dependencias Python
```

## 🔐 Configuración JWT

Tokens configurados en `settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}
```

## 📖 Historias de Usuario Implementadas

### HU-01: Registro de Usuarios

- ✅ Formulario de registro con validación
- ✅ Campos: nombre, apellido, email, número de documento, contraseña
- ✅ Validación de formato de email
- ✅ Requisitos de contraseña: mínimo 8 caracteres, letra mayúscula, número
- ✅ Asignación automática de rol "Estudiante"

### HU-02: Login de Usuarios

- ✅ Login con email y contraseña
- ✅ Generación de tokens JWT (access + refresh)
- ✅ Validación de usuario activo
- ✅ Mensajes de error claros (credenciales incorrectas, usuario inactivo)
- ✅ Renovación automática de tokens
- ✅ Cierre de sesión con limpieza de tokens

### HU-06: Creación/gestión de Asignaturas (módulo académico)

- ✅ Campos: nombre, código (único), descripción, estado, fecha_creacion, periodo_academico
- ✅ Activar/desactivar por `estado`
- ✅ Asignación de docentes implementada vía tabla intermedia `ProfesorAsignatura` (no campo `docente_responsable`)
- ✅ Notificación al asignar docente vía señales (ver `applications/academico/signals.py`)

## 🛠️ Tecnologías Utilizadas

- **Django 5.2** - Framework web
- **Django REST Framework** - API REST
- **Simple JWT** - Autenticación JWT
- **PostgreSQL** - Base de datos
- **drf-spectacular** - Documentación OpenAPI
- **Celery + Redis** - Tareas asíncronas (opcional)
- **Pillow** - Procesamiento de imágenes

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de uso educativo.

## 👤 Autor

**Christian LAMBDA**

- GitHub: [@Crhistian-LAMBDA](https://github.com/Crhistian-LAMBDA)

---

Para más información, consulta la [Guía de Replicación](docs/Guia_Replicacion_Proyecto.md).

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
