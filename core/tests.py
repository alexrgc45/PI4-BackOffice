from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone as django_timezone
from rest_framework.test import APIClient

from .models import (
    Administrador,
    Cliente,
    Colaborador,
    Encomenda,
    PermissaoColaborador,
    TipoTrabalho,
    Trabalho,
    Utilizador,
)


class DashboardTests(TestCase):
    def test_login_page_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bem-vindo de volta")

    def test_dashboard_loads(self):
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visão geral")
        self.assertContains(response, "/static/js/admin-dashboard.js")

    def test_admin_work_list_loads(self):
        response = self.client.get("/trabalhos/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Todos os trabalhos")
        self.assertContains(response, "/static/js/admin-work-list.js")


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
            criado_em=datetime.now(datetime_timezone.utc),
            atualizado_em=datetime.now(datetime_timezone.utc),
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
            criado_em=datetime.now(datetime_timezone.utc),
            atualizado_em=datetime.now(datetime_timezone.utc),
        )

        response = self.client.post(
            "/api/v1/auth/token/",
            {"email": "teste@example.com", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    @patch(
        "core.api.serializers.get_user_permissions",
        return_value=["rececao_trabalhos"],
    )
    @patch("core.api.serializers.get_user_role", return_value="administrador")
    @patch("core.api.authentication.Utilizador.objects.get")
    def test_profile_returns_authenticated_user(
        self,
        get_user,
        get_role,
        get_permissions,
    ):
        user = Utilizador(
            id=1,
            email="teste@example.com",
            password_hash=make_password("password-123"),
            ativo=True,
            criado_em=datetime.now(datetime_timezone.utc),
            atualizado_em=datetime.now(datetime_timezone.utc),
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
        self.assertEqual(response.data["perfil"], "administrador")
        self.assertEqual(response.data["permissoes"], ["rececao_trabalhos"])


class WorkAccessApiTests(TransactionTestCase):
    schema_models = (
        Utilizador,
        Administrador,
        Colaborador,
        Cliente,
        Encomenda,
        TipoTrabalho,
        Trabalho,
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            for model in cls.schema_models:
                schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            for model in reversed(cls.schema_models):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self):
        PermissaoColaborador.objects.all().delete()
        Trabalho.objects.all().delete()
        Encomenda.objects.all().delete()
        Cliente.objects.all().delete()
        Colaborador.objects.all().delete()
        Administrador.objects.all().delete()
        TipoTrabalho.objects.all().delete()
        Utilizador.objects.all().delete()

        self.api = APIClient()
        self.admin = self.create_user("admin@example.com")
        Administrador.objects.create(utilizador=self.admin, nome="Admin")
        self.collaborator = self.create_user("tecnico@example.com")
        Colaborador.objects.create(
            utilizador=self.collaborator,
            nome="Técnico",
            ativo=True,
        )
        self.client_one = self.create_client("cliente1@example.com", "111111111")
        self.client_two = self.create_client("cliente2@example.com", "222222222")
        self.work_type = TipoTrabalho.objects.create(nome="Coroa", ativo=True)

        self.client_work = self.create_work(self.client_one, "Por Iniciar")
        self.other_client_work = self.create_work(self.client_two, "Por Iniciar")
        self.completed_work = self.create_work(self.client_one, "Concluído")
        self.review_work = self.create_work(self.client_one, "Em Avaliação")
        self.pending_order = Encomenda.objects.create(
            cliente=self.client_one,
            criada_por=self.admin,
            paciente_nome="Novo pedido",
            estado="Em Avaliação",
            data_criacao=django_timezone.now(),
        )

    def create_user(self, email):
        now = django_timezone.now()
        return Utilizador.objects.create(
            email=email,
            password_hash=make_password("test-password"),
            ativo=True,
            criado_em=now,
            atualizado_em=now,
        )

    def create_client(self, email, nif):
        user = self.create_user(email)
        return Cliente.objects.create(
            utilizador=user,
            nome=email,
            nif=nif,
            tem_conta=True,
            ativo=True,
        )

    def create_work(self, client, state):
        now = django_timezone.now()
        order = Encomenda.objects.create(
            cliente=client,
            criada_por=self.admin,
            paciente_nome=f"Paciente {client.pk} {state}",
            estado="Aceite",
            data_criacao=now,
        )
        return Trabalho.objects.create(
            encomenda=order,
            tipo_trabalho=self.work_type,
            natureza="Prótese fixa",
            estado=state,
            criado_em=now,
            atualizado_em=now,
        )

    def test_client_only_sees_works_for_own_clinic(self):
        self.api.force_authenticate(user=self.client_one.utilizador)

        response = self.api.get("/api/v1/trabalhos/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in response.data},
            {
                self.client_work.pk,
                self.completed_work.pk,
                self.review_work.pk,
            },
        )

    def test_client_cannot_retrieve_another_clinics_work(self):
        self.api.force_authenticate(user=self.client_one.utilizador)

        response = self.api.get(
            f"/api/v1/trabalhos/{self.other_client_work.pk}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_collaborator_sees_operational_works_but_not_history_or_review(self):
        self.api.force_authenticate(user=self.collaborator)

        response = self.api.get("/api/v1/trabalhos/")

        self.assertEqual(response.status_code, 200)
        visible_ids = {item["id"] for item in response.data}
        self.assertEqual(
            visible_ids,
            {self.client_work.pk, self.other_client_work.pk},
        )

    def test_administrator_sees_all_works(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.get("/api/v1/trabalhos/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)

    def test_account_without_a_profile_cannot_list_works(self):
        user = self.create_user("sem-perfil@example.com")
        self.api.force_authenticate(user=user)

        response = self.api.get("/api/v1/trabalhos/")

        self.assertEqual(response.status_code, 403)

    def test_work_endpoint_does_not_allow_writes_yet(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.post("/api/v1/trabalhos/", {}, format="json")

        self.assertEqual(response.status_code, 405)

    def test_collaborator_without_reception_permission_is_denied(self):
        self.api.force_authenticate(user=self.collaborator)

        response = self.api.get("/api/v1/encomendas/rececao/")

        self.assertEqual(response.status_code, 403)

    def test_administrator_can_grant_and_revoke_reception_permission(self):
        self.api.force_authenticate(user=self.admin)
        url = f"/api/v1/permissoes/colaboradores/{self.collaborator.pk}/"

        grant_response = self.api.post(
            url,
            {"codigo": PermissaoColaborador.Codigo.RECECAO_TRABALHOS},
            format="json",
        )
        duplicate_response = self.api.post(
            url,
            {"codigo": PermissaoColaborador.Codigo.RECECAO_TRABALHOS},
            format="json",
        )

        self.assertEqual(grant_response.status_code, 201)
        self.assertEqual(duplicate_response.status_code, 201)
        self.assertEqual(PermissaoColaborador.objects.count(), 1)

        revoke_response = self.api.delete(
            f"{url}{PermissaoColaborador.Codigo.RECECAO_TRABALHOS}/"
        )

        self.assertEqual(revoke_response.status_code, 204)
        self.assertEqual(PermissaoColaborador.objects.count(), 0)

    def test_reception_permission_exposes_only_pending_orders(self):
        PermissaoColaborador.objects.create(
            colaborador_id=self.collaborator.pk,
            codigo=PermissaoColaborador.Codigo.RECECAO_TRABALHOS,
            concedida_por=self.admin,
        )
        self.api.force_authenticate(user=self.collaborator)

        response = self.api.get("/api/v1/encomendas/rececao/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data],
            [self.pending_order.pk],
        )

    def test_client_cannot_manage_collaborator_permissions(self):
        self.api.force_authenticate(user=self.client_one.utilizador)

        response = self.api.post(
            f"/api/v1/permissoes/colaboradores/{self.collaborator.pk}/",
            {"codigo": PermissaoColaborador.Codigo.RECECAO_TRABALHOS},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
