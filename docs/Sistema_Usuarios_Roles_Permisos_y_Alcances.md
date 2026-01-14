# Sistema de Usuarios, Roles, Permisos y Alcances (Implementación actual)

Fecha de análisis: 12-01-2026

Este documento describe **cómo funciona hoy** (según el código) el sistema de:

- Autenticación (JWT)
- Registro y aprobación de usuarios
- Roles (multi-rol) + compatibilidad con rol legado
- Permisos granulares por “acción”
- Alcances por **facultad**, **carrera**, **asignaturas** y **matrículas**
- Restricciones de UI (qué se muestra/oculta en el frontend)

> Importante: el proyecto combina dos mecanismos de rol:
>
> 1. `Usuario.roles` (ManyToMany a `Rol`) **(nuevo)**
> 2. `Usuario.rol` (string) **(legacy/compatibilidad)**
>
> En muchos filtros del backend todavía se usa `user.rol` para decisiones de negocio, por lo que es crítico que el rol legacy se mantenga sincronizado con el rol “principal”.

---

## 1) Componentes principales

### Backend (Django/DRF)

- Modelo de usuario personalizado: `applications.usuarios.models.Usuario` (extiende `AbstractUser`).
- JWT: `djangorestframework-simplejwt`.
- Permisos granulares:
  - `applications.usuarios.models.Permiso` (códigos: `crear_asignatura`, `ver_usuarios`, etc.).
  - `applications.usuarios.models.Rol` con `permisos_asignados` (M2M).
  - `Usuario.tiene_permiso(codigo)` resuelve permisos vía roles.
  - `applications.usuarios.api.permissions.TienePermiso` se usa en ViewSets para bloquear acciones por permiso.

### Frontend (React)

- Contexto auth: `src/hooks/AuthContext.js`.
- Guardia de rutas: `src/shared/components/ProtectedRoute.js`.
- Menú/visibilidad por rol (UI): `src/layouts/AppLayout.js`.
- Mapeo de nombres “bonitos” de roles: `src/shared/utils/roleDisplayNames.js`.

---

## 2) Roles existentes y jerarquía (HU-05)

### Roles “técnicos” (los que viajan por API)

- `super_admin`
- `admin`
- `coordinador`
- `profesor`
- `estudiante`

> Nota: existe el alias `docente` en algunas partes para compatibilidad, pero el rol real del proyecto es `profesor`.

### Jerarquía

Backend define una jerarquía numérica (mayor = más poder):

- `super_admin`: 5
- `admin`: 4
- `coordinador`: 3
- `profesor`: 2
- `estudiante`: 1

Reglas clave implementadas en `Usuario`:

- `get_rol_principal()`: obtiene el rol más alto considerando `roles` (M2M) y `rol` legacy.
- `get_nivel_jerarquia()`: nivel del usuario.
- `puede_asignar_rol(target_role)`: **solo** permite asignar roles de nivel estrictamente menor.
- `puede_editar_usuario(target_user)`: solo permite editar usuarios de nivel inferior.

Esto soporta el principio: “no puedes crear/editar/elevar a alguien a tu mismo nivel o superior”.

---

## 3) Permisos granulares por “acción”

### ¿Qué es un permiso?

Un permiso es un registro `Permiso` con un `codigo` único. Ejemplos:

- `ver_usuarios`
- `crear_usuario`
- `editar_usuario`
- `eliminar_usuario`
- `ver_asignaturas`
- `crear_asignatura`
- `calificar_tarea`
- `ver_notas` / `editar_notas`

Los permisos se agrupan por módulo (`academico`, `usuarios`, `reportes`, `notificaciones`).

Los permisos iniciales se crean con el comando:

- `python manage.py crear_permisos`

Y se asignan a roles con:

- `python manage.py asignar_permisos_roles`

### ¿Cómo se evalúa un permiso?

- `Usuario.tiene_permiso(codigo_permiso)`:
  - Si `is_superuser` o tiene rol `super_admin` -> devuelve **True** siempre.
  - Si no, revisa los `permisos_asignados` de cada `Rol` asociado al usuario.
  - Si el usuario NO tiene roles M2M pero sí `rol` legacy, intenta resolver ese rol contra la tabla `Rol`.

### ¿Dónde se aplica un permiso?

En los ViewSets que usan `permission_classes = [TienePermiso]`.

- Cada ViewSet define (en general) un diccionario `permisos_por_accion`.
- El permiso se decide por `view.action` (list, retrieve, create, update, etc.).
- Si una acción no tiene permiso definido, la clase **niega por seguridad**.

Ejemplo real: `FacultadViewSet` en Académico.

---

## 4) Flujo de vida de un usuario (Registro → Aprobación → Uso)

### Registro

En esta implementación, el registro está diseñado para crear usuarios “pendientes”:

- El usuario se crea SIEMPRE:
  - `is_active = False`
  - `estado = 'inactivo'`
  - **sin roles**

El cliente NO puede forzar rol/estado en el registro: el serializer ignora esos campos.

Endpoints:

- `POST /api/auth/registro/`
- `POST /api/usuarios/registro/` (alias compat)

### Login

Para iniciar sesión:

- se busca usuario por `email`
- se valida password
- se valida que esté activo (`is_active == True` y `estado != inactivo`)
- se valida que tenga al menos un rol (M2M) o `rol` legacy

Endpoints:

- `POST /api/auth/login/`
- `POST /api/usuarios/login/` (alias compat)

### Aprobación (activar y asignar roles)

Existe un endpoint explícito para aprobar usuarios nuevos:

- `POST /api/auth/aprobar-usuario/`

Reglas:

- Solo `super_admin` o `admin` pueden aprobar.
- Aplica HU-05: no puedes asignar roles iguales/superiores al aprobador.
- Asigna roles en `Usuario.roles`.
- Sincroniza rol legacy (`Usuario.rol`) al rol más alto de la lista.
- Puede asignar `facultad` (por `facultad_id`).
- Activa cuenta (`is_active=True`, `estado='activo'`).

Además, el `UsuarioViewSet.partial_update` también sincroniza `estado` e `is_active` y envía correo cuando pasa de inactivo→activo.

---

## 5) Alcances por Facultad/Carrera/Asignaturas (reglas reales por rol)

Esta sección es la “deducción importante”: no basta con tener permiso, también existe **alcance** (scope) por facultad/carrera/materias.

### 5.1 Facultades (`/api/facultades/`)

- `super_admin`: ve todas.
- `admin`: ve solo su `user.facultad`.
- `coordinador`: ve solo su `user.facultad`.
- otros: el código no restringe explícitamente el queryset a none, pero el permiso `ver_facultades` normalmente limita el acceso por rol.

### 5.2 Asignaturas (`/api/asignaturas/`)

Regla por rol:

- `super_admin`: todas.
- `admin`: asignaturas cuya(s) carrera(s) pertenecen a su facultad.
- `coordinador`: igual que admin (por facultad).
- `profesor/docente`: SOLO sus asignaturas via tabla `ProfesorAsignatura`.
- `estudiante`: asignaturas activas (`estado=True`) de su `user.carrera`.

Esto implementa “profesor limitado por materias a cargo” y “estudiante limitado por carrera”.

### 5.3 Matrículas (`/api/matriculas/`)

`MatriculaViewSet.get_queryset`:

- `super_admin`: ve todo.
- `admin/coordinador`: ve matrículas de estudiantes cuya carrera pertenece a su facultad.
- `estudiante`: ve solo sus matrículas.

`MatriculaViewSet.perform_create`:

- Solo un estudiante puede crear matrícula “para sí mismo” (se fuerza `estudiante=user`).
- La asignatura debe:
  - estar activa
  - pertenecer al periodo indicado
  - estar asociada a la carrera del estudiante
- evita duplicados por (estudiante, asignatura, periodo)

Endpoint adicional:

- `GET /api/matriculas/disponibles/`: retorna asignaturas activas de la carrera del estudiante NO matriculadas en el periodo activo.

### 5.4 Tareas y calificaciones (Evaluaciones)

Hay dos tipos de vistas:

#### A) Staff: docentes/coordinadores/admin/super_admin

- `TareaViewSet.get_queryset`:

  - `super_admin`: todas.
  - `admin/coordinador`: tareas de asignaturas de su facultad.
  - `profesor/docente`: tareas de SUS asignaturas (via `ProfesorAsignatura`).

- `GET /api/staff-calificaciones/`:
  - permitido a `profesor/docente/coordinador/admin/super_admin`
  - la lista se deriva desde `ProfesorAsignatura` + periodo (activo o `periodo_id`).
  - alcance:
    - super_admin: todo
    - admin/coordinador: por facultad
    - profesor/docente: solo él

#### B) Estudiante

- `GET /api/mis-tareas/`:

  - SOLO estudiantes.
  - retorna tareas de asignaturas donde:
    - el estudiante tiene matrícula
    - y el campo `horario` no está vacío

- `GET /api/mis-calificaciones/`:
  - SOLO estudiantes.
  - construye un resumen por asignatura (periodo, horario, docentes asignados, tareas y notas).

Esta es exactamente la lógica que mencionabas: hay vistas que solo tienen sentido para el estudiante (subir/ver su progreso), aunque técnicamente un super_admin podría “verlo” si se le habilitara (hoy está bloqueado por rol).

---

## 6) Gestión de usuarios (CRUD) y limitaciones

### Endpoints principales

- `GET /api/usuarios/` (lista)
- `GET /api/usuarios/{id}/`
- `PATCH /api/usuarios/{id}/`
- `DELETE /api/usuarios/{id}/`
- `GET /api/usuarios/me/`

### Permisos granulares por acción (UsuarioViewSet)

`UsuarioViewSet.permisos_por_accion`:

- `list`, `retrieve` -> `ver_usuarios`
- `create` -> `crear_usuario`
- `update`, `partial_update` -> `editar_usuario`
- `destroy` -> `eliminar_usuario`
- `me` -> `None` (solo autenticación)

### Reglas de edición

- Un usuario normal editando SU PERFIL:

  - solo puede cambiar `first_name`, `last_name`, `email`.
  - no puede cambiar roles, facultad, carrera, estado, etc.

- Edición de terceros:
  - se aplica HU-05 (`puede_editar_usuario`).
  - se sincroniza `estado` ↔ `is_active`.
  - si pasa de inactivo a activo, dispara correo.

### Filtrado en listado (scope)

`UsuarioViewSet.get_queryset` para `list` aplica:

- `super_admin`: ve todos.
- `admin`: ve usuarios “de su facultad” (con un caso especial que incluye `facultad__isnull=True`).
- `coordinador`: similar.
- otros: solo se ven a sí mismos.

Además, hay un filtro jerárquico HU-05 sobre el rol legacy que evita listar usuarios de igual/superior jerarquía (salvo el propio usuario).

---

## 7) Roles y permisos (administración)

### Roles (`/api/roles/`)

`RolViewSet`:

- lectura: cualquier usuario autenticado.
- crear/editar/eliminar/actualizar permisos: SOLO `super_admin`.

Endpoint adicional:

- `PUT /api/roles/{id}/permisos/` con `permisos_ids`.

### Permisos (`/api/permisos/`)

`PermisoViewSet`:

- solo lectura.
- lista todos los permisos activos.

---

## 8) Frontend: cómo se “ocultan” o protegen pantallas

La UI tiene 2 capas:

1. **Protección de rutas** (navegación) con `ProtectedRoute`.
2. **Visibilidad del menú** (qué items aparecen) con lógica por rol.

### 8.1 ProtectedRoute

- Si no hay sesión → redirige a `/login`.
- Si se define `allowedRoles`:
  - toma `user.roles` (lista) o `user.rol` (legacy) como fallback.
  - si el usuario no tiene ninguno → redirige a `/dashboard`.

### 8.2 Menú principal (AppLayout)

Existe una función `tieneAlgunRol([...])` que decide qué se muestra.

Resumen (UI):

- `Usuarios` (pantalla de gestión): solo `admin` y `super_admin`.
- `Roles y Permisos`: solo `super_admin`.
- `Asignaturas`: `admin`, `super_admin`, `coordinador`.
- `Facultades`: `admin`, `super_admin`.
- `Carreras`: `admin`, `super_admin`, `coordinador`.
- `Periodos Académicos`: `super_admin`, `admin`, `coordinador`.
- Staff académico:
  - `Tareas`, `Notas por Materia`, `Entregas de Estudiantes`: `profesor/docente/coordinador/admin/super_admin`.
- Estudiante:
  - `Matricular Asignaturas`, `Mis Asignaturas`, `Mis Tareas`, `Mis Calificaciones`: solo `estudiante`.

> Nota importante: la UI “oculta” opciones, pero la seguridad real está en el backend.

---

## 9) Conclusiones prácticas (lo que hoy ya está resuelto)

- El proyecto NO es solo RBAC (rol → pantalla). Es:

  - RBAC (rol)
  - - permisos granulares (`Permiso`)
  - - scopes por facultad/carrera/asignaturas/matrículas
  - - reglas jerárquicas HU-05

- Flujo de registro seguro:

  - registro crea usuario inactivo sin roles
  - admin/super_admin aprueba y asigna roles

- Profesor realmente está limitado por materias asignadas (tabla `ProfesorAsignatura`).
- Estudiante está limitado por carrera y por sus matrículas (y en vistas de tareas/calificaciones se exige `horario`).

---

## 10) Checklist rápido para “aplicar funcionalidades” sin romper el sistema

Cuando implementemos nuevas features, conviene responder siempre estas preguntas:

1. ¿Se protege por permiso (`TienePermiso` + `permisos_por_accion`)?
2. ¿Cuál es el scope por rol?
   - super_admin global
   - admin/coordinador por `user.facultad`
   - profesor por `ProfesorAsignatura`
   - estudiante por `user.carrera` + `Matricula`
3. ¿La UI debe ocultarla por rol?
4. ¿El endpoint debe permitir super_admin aunque normalmente “no lo use”? (decisión de negocio)

---

## Anexo: Endpoints clave (por módulo)

### Usuarios/Auth

- `POST /api/auth/registro/`
- `POST /api/auth/login/`
- `POST /api/auth/cambiar-password/`
- `POST /api/auth/solicitar-recuperacion/`
- `POST /api/auth/resetear-password/`
- `POST /api/auth/validar-token/`
- `POST /api/auth/aprobar-usuario/`

- `GET /api/usuarios/me/`
- `GET /api/usuarios/`
- `PATCH /api/usuarios/{id}/`
- `DELETE /api/usuarios/{id}/`

- `GET /api/roles/`
- `PUT /api/roles/{id}/permisos/`
- `GET /api/permisos/`

### Académico

- `GET /api/facultades/`
- `GET /api/carreras/`
- `GET /api/asignaturas/`
- `POST /api/asignaturas/importar/`
- `POST /api/periodos-academicos/{id}/activar/`

### Matrículas

- `GET /api/matriculas/`
- `POST /api/matriculas/`
- `GET /api/matriculas/disponibles/`

### Evaluaciones

- `GET /api/tareas/`
- `POST /api/tareas/`
- `GET /api/entregas/`
- `GET /api/mis-tareas/`
- `GET /api/mis-calificaciones/`
- `GET /api/staff-calificaciones/`
