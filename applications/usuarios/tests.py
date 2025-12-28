from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from applications.usuarios.models import Facultad, Programa, Asignatura, ProfesorAsignatura
from unittest.mock import patch


class UsuarioAPITests(APITestCase):
	def setUp(self):
		self.client = APIClient()
		self.User = get_user_model()

		# Datos académicos base
		self.facultad = Facultad.objects.create(nombre="Ingeniería")
		self.programa = Programa.objects.create(
			nombre="Sistemas", codigo="SIS-01", facultad=self.facultad
		)
		self.asig1 = Asignatura.objects.create(nombre="Algoritmos", codigo="ALG-01")
		self.asig2 = Asignatura.objects.create(nombre="Bases", codigo="BAS-01")

		# Usuarios base
		self.super_admin = self.User.objects.create_user(
			username="super", password="pass1234", rol="super_admin"
		)
		self.admin = self.User.objects.create_user(
			username="admin1", email="admin1@example.com", password="pass1234", rol="admin", facultad=self.facultad
		)
		self.admin2 = self.User.objects.create_user(
			username="admin2", password="pass1234", rol="admin"
		)
		self.profesor = self.User.objects.create_user(
			username="prof1", password="pass1234", rol="profesor"
		)
		self.estudiante = self.User.objects.create_user(
			username="estu1", password="pass1234", rol="estudiante", programa=self.programa
		)

	def test_registro_estudiante(self):
		url = "/api/usuarios/registro/"
		payload = {
			"username": "nuevo_est",
			"email": "nuevo@example.com",
			"first_name": "Nuevo",
			"last_name": "Estudiante",
			"numero_documento": "1234567890",
			"password": "Pass1234",
			"password_confirm": "Pass1234",
			"rol": "estudiante",
			"estado": "activo",
		}
		resp = self.client.post(url, payload, format="json")
		self.assertEqual(resp.status_code, 201)
		self.assertTrue(self.User.objects.filter(username="nuevo_est").exists())
		self.assertEqual(
			self.User.objects.get(username="nuevo_est").numero_documento,
			"1234567890",
		)

	def test_login_ok_devuelve_tokens(self):
		url = "/api/usuarios/login/"
		resp = self.client.post(url, {"email": "admin1@example.com", "password": "pass1234"}, format="json")
		self.assertEqual(resp.status_code, 200)
		self.assertIn("access", resp.data)
		self.assertIn("refresh", resp.data)
		self.assertEqual(resp.data["usuario"]["username"], "admin1")

	def test_admin_no_puede_editar_admin(self):
		self.client.force_authenticate(user=self.admin)
		url = f"/api/usuarios/{self.admin2.id}/"
		resp = self.client.patch(url, {"first_name": "Bloqueado"}, format="json")
		self.assertEqual(resp.status_code, 403)

	def test_super_admin_si_puede_editar_admin(self):
		self.client.force_authenticate(user=self.super_admin)
		url = f"/api/usuarios/{self.admin2.id}/"
		resp = self.client.patch(url, {"first_name": "Permitido"}, format="json")
		self.assertEqual(resp.status_code, 200)
		self.admin2.refresh_from_db()
		self.assertEqual(self.admin2.first_name, "Permitido")

	def test_admin_no_puede_eliminar_admin(self):
		self.client.force_authenticate(user=self.admin)
		url = f"/api/usuarios/{self.admin2.id}/"
		resp = self.client.delete(url)
		self.assertEqual(resp.status_code, 403)
		self.assertTrue(self.User.objects.filter(id=self.admin2.id).exists())

	def test_super_admin_asigna_asignaturas_a_profesor(self):
		self.client.force_authenticate(user=self.super_admin)
		url = f"/api/usuarios/{self.profesor.id}/"
		payload = {"asignaturas_ids": [self.asig1.id, self.asig2.id], "rol": "profesor"}
		resp = self.client.patch(url, payload, format="json")
		self.assertEqual(resp.status_code, 200)
		rels = ProfesorAsignatura.objects.filter(profesor=self.profesor)
		self.assertEqual(rels.count(), 2)

	@patch('django.core.mail.send_mail')
	def test_cambiar_password_envia_correo(self, mock_send_mail):
		"""Verifica que cambiar contraseña envía un correo de confirmación"""
		self.client.force_authenticate(user=self.admin)
		url = "/api/usuarios/cambiar_password/"
		payload = {
			"password_actual": "pass1234",
			"password_nuevo": "NewPass123",
			"password_nuevo_confirm": "NewPass123"
		}
		resp = self.client.post(url, payload, format="json")
		
		# Verificar que la respuesta fue exitosa
		self.assertEqual(resp.status_code, 200)
		self.assertIn("correo de confirmación", resp.data["detail"].lower())
		
		# Verificar que send_mail fue llamado
		self.assertTrue(mock_send_mail.called)
		
		# Verificar los argumentos de la llamada
		call_args = mock_send_mail.call_args
		self.assertIn("Contraseña cambiada", call_args[0][0])  # asunto
		# La lista de destinatarios es el 4º argumento (índice 3)
		self.assertIn(self.admin.email, call_args[0][3])  # email destinatario en lista
