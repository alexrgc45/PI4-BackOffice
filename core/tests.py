from datetime import datetime, timezone
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Utilizador


class DashboardTests(TestCase):
    def test_dashboard_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestão do laboratório")


class ApiAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_profile_requires_authentication(self):
        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 401)

    @patch("core.api.serializers.Utilizador.objects.get")
    def test_token_login_returns_jwt_for_active_user(self, get_user):
        user = Utilizador(
            id=1,
            email="teste@example.com",
            password_hash=make_password("password-123"),
            ativo=True,
            criado_em=datetime.now(timezone.utc),
            atualizado_em=datetime.now(timezone.utc),
        )
        get_user.return_value = user

        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": "teste@example.com", "password": "password-123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    @patch("core.api.serializers.Utilizador.objects.get")
    def test_token_login_rejects_invalid_password(self, get_user):
        get_user.return_value = Utilizador(
            id=1,
            email="teste@example.com",
            password_hash=make_password("different-password"),
            ativo=True,
            criado_em=datetime.now(timezone.utc),
            atualizado_em=datetime.now(timezone.utc),
        )

        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": "teste@example.com", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    @patch("core.api.authentication.Utilizador.objects.get")
    def test_profile_returns_authenticated_user(self, get_user):
        user = Utilizador(
            id=1,
            email="teste@example.com",
            password_hash=make_password("password-123"),
            ativo=True,
            criado_em=datetime.now(timezone.utc),
            atualizado_em=datetime.now(timezone.utc),
        )
        get_user.return_value = user
        token = self.client.post(
            "/api/v1/auth/token/",
            {"email": "teste@example.com", "password": "password-123"},
            format="json",
        )

        get_user.return_value = user
        response = self.client.get(
            "/api/v1/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {token.data['access']}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "teste@example.com")
