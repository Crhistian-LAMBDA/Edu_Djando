# Matriz de pruebas (permisos + alcance por facultad)

Objetivo: validar que el acceso a vistas/endpoints respeta la jerarquía de roles y el alcance por facultad/carrera.

## Preparación mínima de datos

- Facultades: F1, F2
- Carreras: C1 (de F1), C2 (de F2)
- Período activo: P1
- Asignaturas:
  - A1 (de C1/F1, en P1)
  - A2 (de C2/F2, en P1)
- Usuarios:
  - U_super (rol: super_admin)
  - U_admin_F1 (rol: admin, `facultad=F1`)
  - U_coord_F1 (rol: coordinador, `facultad=F1`)
  - U_prof_A1 (rol: profesor, asignado a A1 vía ProfesorAsignatura)
  - U_est_C1 (rol: estudiante, `carrera=C1`)
  - U_est_C2 (rol: estudiante, `carrera=C2`)
- Matrículas:
  - U_est_C1 matriculado en A1, período P1, con `horario` NO vacío
  - U_est_C2 matriculado en A2, período P1, con `horario` NO vacío

## Reglas esperadas (resumen)

- super_admin: ve/ejecuta todo.
- admin/coordinador: CRUD dentro de su facultad; fuera de su facultad NO debe ver/ejecutar.
- profesor: solo lo de sus asignaturas.
- estudiante: solo lo de su carrera/matrícula.

## Casos de prueba (API)

### 1) Asignaturas (list)

Endpoint sugerido: `GET /api/asignaturas/`

- U_super: debe ver A1 y A2.
- U_admin_F1: debe ver solo A1.
- U_coord_F1: debe ver solo A1.
- U_prof_A1: debe ver solo A1.
- U_est_C1: debe ver solo A1.
- U_est_C2: debe ver solo A2.

### 2) Carreras (list)

Endpoint sugerido: `GET /api/carreras/`

- U_super: debe ver C1 y C2.
- U_admin_F1: debe ver solo C1.
- U_coord_F1: debe ver solo C1.

### 3) Planes carrera-asignatura (list)

Endpoint sugerido: `GET /api/plan-carrera-asignatura/` (o el que uses en router)

- U_super: ve todos.
- U_admin_F1: solo planes de carreras de F1.
- U_coord_F1: solo planes de carreras de F1.

### 4) Matrículas (list)

Endpoint: `GET /api/matriculas/`

- U_super: ve todas las matrículas.
- U_admin_F1: ve solo matrículas de estudiantes cuya carrera pertenece a F1.
- U_coord_F1: ve solo matrículas de F1.
- U_est_C1: ve solo sus matrículas.

### 5) Matrícula disponibles (por carrera + período activo)

Endpoint: `GET /api/matriculas/disponibles/`

- U_est_C1: solo debe devolver asignaturas de C1/F1 en P1.
- U_est_C2: solo debe devolver asignaturas de C2/F2 en P1.

### 6) Staff calificaciones (alcance por facultad)

Endpoint: `GET /api/staff-calificaciones/?periodo_id=P1`

- U_super: ve asignaturas de F1 y F2.
- U_admin_F1: solo ve asignaturas de F1.
- U_coord_F1: solo ve asignaturas de F1.
- U_prof_A1: solo ve asignaturas donde él está asignado (A1).

### 7) Tareas (list) por rol

Endpoint: `GET /api/tareas/`

- U_super: ve tareas de A1 y A2.
- U_admin_F1: solo ve tareas de asignaturas de F1.
- U_coord_F1: solo ve tareas de asignaturas de F1.
- U_prof_A1: solo ve tareas de A1.
- U_est_C1: solo ve tareas de asignaturas donde tiene matrícula y `horario` no vacío.

### 8) HU-09 - Entregas: calificar (acción)

Endpoint: `POST /api/entregas/{id}/calificar/`

Precondición:

- Existe una entrega `E1` de una tarea de A1 (F1) hecha por U_est_C1.

Casos:

- U_super: puede calificar cualquier entrega (incluye E1).
- U_admin_F1: puede calificar E1 (misma facultad).
- U_coord_F1: puede calificar E1 (misma facultad).
- U_prof_A1: puede calificar E1 (profesor asignado a A1).
- U_est_C1: NO puede calificar (403).
- U_est_C2: NO puede calificar (403).
- U_admin_F1 / U_coord_F1 intentando calificar una entrega de F2: NO debe poder (403).

Payloads válidos (compat):

- Forma estándar:
  - `{ "calificacion": 85.5, "comentarios_docente": "Excelente trabajo" }`
- Aliases HU-09 (sin romper compat):
  - `{ "nota": 85.5, "retroalimentacion_docente": "Excelente trabajo" }`

Validaciones esperadas:

- Si falta calificación/nota: 400.
- Si calificación < 0 o > 100: 400.
- Si calificación no es número: 400.

Efectos esperados al calificar:

- `estado_entrega` pasa a `calificada`.
- `fecha_calificacion` se setea.
- El response incluye `entrega` con aliases en salida (p.ej. `nota`, `retroalimentacion_docente`, `estado_calificacion`).
- Se encola notificación al estudiante (requiere Celery worker + SMTP/Email backend activo para observar el envío real).

### 9) HU-09 - Estudiante: mis calificaciones (ponderado)

Endpoint: `GET /api/mis-calificaciones/`

Casos:

- U_est_C1: solo ve calificaciones/entregas asociadas a sus asignaturas (A1).
- U_est_C2: solo ve calificaciones/entregas asociadas a sus asignaturas (A2).
- U_super / U_admin_F1 / U_coord_F1 / U_prof_A1: NO deberían usar este endpoint (si lo consumen, validar que no exponga datos indebidos).

Verificaciones mínimas:

- Las entregas calificadas exponen `nota`, `retroalimentacion_docente` y `estado_calificacion` en el payload (aliases).
- El ponderado/cálculo mostrado corresponde a los pesos definidos en BD para las tareas del período/asignatura (si existen tareas con diferentes pesos, el resultado debe reflejarlo).

## Casos de prueba (UI)

### 10) Menú/Visibilidad de formularios

Validar que el menú muestre formularios según rol y que el contenido cargado no “filtre” datos de otra facultad:

- U_super: debe poder entrar a todos los módulos.
- U_admin_F1 / U_coord_F1: debe poder entrar a Académico; dentro solo ver datos de F1.
- U_prof_A1: módulos del profesor; dentro solo A1.
- U_est_C1: Matrícula/Mis tareas/Mis asignaturas; dentro solo C1.

## HU-09 (Frontend) - Calificación y visualización de notas

### Descripción

Como **docente/staff** quiero **calificar entregas** para que el **estudiante** pueda **ver su nota y avance ponderado** por materia.

### Pantallas/Flujos existentes (alineados al backend)

1. **Docente califica una entrega**

- Ruta UI: `GET /profesor/entregas`
- Acción: abrir modal “Calificar” en una entrega y guardar.
- Llama a: `POST /api/entregas/{id}/calificar/` enviando `{ calificacion, comentarios_docente }`.
- Resultado esperado: la entrega queda con `estado_entrega=calificada` y la nota visible en la tabla.

2. **Estudiante revisa sus calificaciones y ponderado**

- Ruta UI: `GET /mis-calificaciones`
- Llama a: `GET /api/mis-calificaciones/`.
- Resultado esperado: ver por materia: `nota_actual_ponderada`, `peso_calificado`, `peso_restante` y el detalle por tarea.

3. **Staff ve resumen por materia (apoyo administrativo)**

- Ruta UI: `GET /staff/calificaciones`
- Llama a: `GET /api/staff-calificaciones/`.
- Resultado esperado: ver estudiantes por asignatura, nota ponderada actual y notas por tarea (según permisos/alcance).

### Criterios de aceptación (Frontend)

1. **Calificación (docente/staff)**

- Desde “Entregas de Estudiantes”, un usuario con rol permitido (profesor/docente y/o staff según alcance) puede calificar una entrega con una nota en rango **0–100** y comentario opcional.
- Si la nota es inválida (vacía/no numérica/fuera de rango), se muestra un error claro y no se envía la calificación.
- Al guardar, la UI refleja la calificación y el estado actualizado de la entrega (sin recargar manualmente la página).

2. **Visualización (estudiante)**

- El estudiante puede ver sus calificaciones en “Mis Calificaciones” sin acceder a datos de otras carreras/asignaturas.
- El ponderado mostrado corresponde a los pesos definidos en el backend (cálculo dinámico), y se actualiza cuando el docente califica.

3. **Permisos y acceso (no romper seguridad por UI)**

- El estudiante no ve acciones de calificación.
- Un usuario sin rol permitido no debe poder usar las pantallas por URL (redirige a dashboard o muestra mensaje de “sin permisos”).

4. **Compatibilidad de payload (backend HU-09)**

- El frontend usa el payload estándar `{ calificacion, comentarios_docente }` y sigue funcionando aunque el backend devuelva aliases en respuesta (`nota`, `retroalimentacion_docente`, `estado_calificacion`).

## Criterio de aprobación

- Ningún rol ve/edita datos fuera de su alcance.
- super_admin siempre puede ver/ejecutar lo que cualquier otro rol puede.
- Si un usuario tiene roles M2M y/o rol legacy, el comportamiento debe ser consistente.
