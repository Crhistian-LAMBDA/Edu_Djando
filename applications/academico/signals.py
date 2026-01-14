
from __future__ import annotations

from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from applications.academico.models import ProfesorAsignatura
from applications.usuarios.tasks import (
    send_asignatura_assignment_email,
    send_asignatura_unassignment_email,
)


def _display_name(user) -> str:
    name = (getattr(user, "get_full_name", lambda: "")() or "").strip()
    return name or getattr(user, "username", "") or "Docente"


def _enqueue_assignment(profesor_asignatura: ProfesorAsignatura) -> None:
    profesor = profesor_asignatura.profesor
    asignatura = profesor_asignatura.asignatura

    docente_email = (profesor.email or "").strip()
    if not docente_email:
        return

    periodo_nombre = ""
    if getattr(asignatura, "periodo_academico", None):
        periodo_nombre = getattr(asignatura.periodo_academico, "nombre", "") or ""

    send_asignatura_assignment_email.delay(
        docente_email=docente_email,
        docente_nombre=_display_name(profesor),
        asignatura_nombre=asignatura.nombre,
        asignatura_codigo=asignatura.codigo,
        periodo_nombre=periodo_nombre,
        descripcion=asignatura.descripcion or "",
    )


def _enqueue_unassignment(profesor, asignatura) -> None:
    docente_email = (getattr(profesor, "email", "") or "").strip()
    if not docente_email:
        return

    periodo_nombre = ""
    if getattr(asignatura, "periodo_academico", None):
        periodo_nombre = getattr(asignatura.periodo_academico, "nombre", "") or ""

    send_asignatura_unassignment_email.delay(
        docente_email=docente_email,
        docente_nombre=_display_name(profesor),
        asignatura_nombre=asignatura.nombre,
        asignatura_codigo=asignatura.codigo,
        periodo_nombre=periodo_nombre,
    )


@receiver(pre_save, sender=ProfesorAsignatura)
def profesor_asignatura_pre_save(sender, instance: ProfesorAsignatura, **kwargs):
    if not instance.pk:
        instance._old_profesor_id = None
        instance._old_asignatura_id = None
        return

    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._old_profesor_id = None
        instance._old_asignatura_id = None
        return

    instance._old_profesor_id = old.profesor_id
    instance._old_asignatura_id = old.asignatura_id


@receiver(post_save, sender=ProfesorAsignatura)
def profesor_asignatura_post_save(sender, instance: ProfesorAsignatura, created: bool, **kwargs):
    if created:
        transaction.on_commit(lambda: _enqueue_assignment(instance))
        return

    old_profesor_id = getattr(instance, "_old_profesor_id", None)
    old_asignatura_id = getattr(instance, "_old_asignatura_id", None)

    # Si alguien edita el registro en lugar de borrar/crear, notificamos el cambio.
    if old_profesor_id and old_profesor_id != instance.profesor_id:
        old_profesor = instance.profesor.__class__.objects.filter(pk=old_profesor_id).first()
        if old_profesor:
            transaction.on_commit(lambda: _enqueue_unassignment(old_profesor, instance.asignatura))
        transaction.on_commit(lambda: _enqueue_assignment(instance))
        return

    if old_asignatura_id and old_asignatura_id != instance.asignatura_id:
        old_asignatura = instance.asignatura.__class__.objects.filter(pk=old_asignatura_id).first()
        if old_asignatura:
            transaction.on_commit(lambda: _enqueue_unassignment(instance.profesor, old_asignatura))
        transaction.on_commit(lambda: _enqueue_assignment(instance))


@receiver(post_delete, sender=ProfesorAsignatura)
def profesor_asignatura_post_delete(sender, instance: ProfesorAsignatura, **kwargs):
    profesor = instance.profesor
    asignatura = instance.asignatura
    transaction.on_commit(lambda: _enqueue_unassignment(profesor, asignatura))
