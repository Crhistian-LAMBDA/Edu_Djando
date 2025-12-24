from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from applications.usuarios.models import Facultad, Asignatura, Programa, ProfesorAsignatura
from .serializar_academico import (
    FacultadSerializer, AsignaturaSerializer, 
    ProgramaSerializer, ProfesorAsignaturaSerializer
)


class FacultadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Facultades"""
    queryset = Facultad.objects.all()
    serializer_class = FacultadSerializer
    permission_classes = [IsAuthenticated]


class AsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Asignaturas"""
    queryset = Asignatura.objects.all()
    serializer_class = AsignaturaSerializer
    permission_classes = [IsAuthenticated]


class ProgramaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Programas"""
    queryset = Programa.objects.all()
    serializer_class = ProgramaSerializer
    permission_classes = [IsAuthenticated]


class ProfesorAsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar relación Profesor-Asignatura"""
    queryset = ProfesorAsignatura.objects.all()
    serializer_class = ProfesorAsignaturaSerializer
    permission_classes = [IsAuthenticated]
