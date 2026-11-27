from datetime import datetime, timedelta, timezone as datetime_timezone
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.utils import timezone as django_timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Administrador,
    Auditoria,
    Cliente,
    Colaborador,
    Convite,
    EtapaTrabalho,
    Encomenda,
    Ficheiro,
    MedicoResponsavel,
    Material,
    Mensagem,
    Notificacao,
    Nota,
    PermissaoColaborador,
    RegistoUtilizador,
    RegistoEtapa,
    TentativaLogin,
    TemplateEtapa,
    TipoTrabalho,
    Trabalho,
    TrabalhoDente,
    TrabalhoMaterial,
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
        self.assertContains(response, "Criar trabalho em nome de cliente")
        self.assertContains(response, 'href="/trabalhos/criar/"')
        self.assertContains(response, "/static/js/admin-work-list.js")

    def test_admin_work_create_page_loads(self):
        response = self.client.get("/trabalhos/criar/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Criar trabalho em nome de cliente")
        self.assertContains(response, "Odontograma")
        self.assertContains(response, "Selecionar todos")
        self.assertContains(response, "Remover todos")
        self.assertContains(response, 'type="file"')
        self.assertContains(response, "/static/js/admin-work-create.js")

    def test_admin_reception_page_loads(self):
        response = self.client.get("/rececao-trabalhos/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Receção de trabalhos")
        self.assertContains(response, "/static/js/admin-reception.js")
        self.assertContains(response, 'href="/rececao-trabalhos/"')

    def test_admin_work_history_page_loads(self):
        response = self.client.get("/historico/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Histórico")
        self.assertContains(response, "/static/js/admin-work-history.js")

    def test_admin_client_page_loads(self):
        response = self.client.get("/clientes/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestão de Clientes")
        self.assertContains(response, "Novo cliente")
        self.assertContains(response, "Clínicas, médicos e pacientes associados")
        self.assertContains(response, "Médicos responsáveis pela clínica")
        self.assertContains(response, 'id="client-detail"')
        self.assertContains(response, 'id="client-rows"')
        self.assertContains(response, 'href="/clientes/criar/"')
        self.assertContains(response, "/static/js/admin-client-list.js")

    def test_admin_client_create_page_loads(self):
        response = self.client.get("/clientes/criar/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Criar cliente")
        self.assertContains(response, "Identificação e contacto")
        self.assertContains(response, 'id="doctor-name"')
        self.assertContains(response, 'id="client-password"')
        self.assertContains(response, 'pattern="[0-9]{9}"')
        self.assertContains(response, "/static/js/admin-client-form.js")

    def test_admin_client_edit_page_loads(self):
        response = self.client.get("/clientes/123/editar/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar cliente")
        self.assertContains(response, 'data-client-id="123"')
        self.assertContains(response, "Guardar alterações")

    def test_admin_collaborator_page_loads(self):
        response = self.client.get("/colaboradores/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Colaboradores")
        self.assertContains(response, "/static/js/admin-collaborator-list.js")
        self.assertContains(response, "Ação")
        self.assertContains(response, 'href="/permissoes/"')

    def test_admin_collaborator_edit_page_loads(self):
        response = self.client.get("/colaboradores/123/editar/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar colaborador")
        self.assertContains(response, 'data-collaborator-id="123"')
        self.assertContains(response, "Guardar alterações")

    def test_admin_pending_user_page_loads(self):
        response = self.client.get("/aceitar-utilizadores/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aceitar utilizadores")
        self.assertContains(response, "/static/js/admin-pending-users.js")

    def test_admin_notification_page_loads(self):
        response = self.client.get("/notificacoes/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notificações")
        self.assertContains(response, "/static/js/admin-notifications.js")

    def test_admin_permissions_page_loads(self):
        response = self.client.get("/permissoes/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Permissões")
        self.assertContains(response, "Receção de trabalhos")
        self.assertContains(response, "/static/js/admin-permissions.js")

    def test_admin_stage_configuration_page_loads(self):
        response = self.client.get("/configuracao-etapas/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configuração de etapas")
        self.assertContains(response, "/static/js/admin-stage-configuration.js")

    def test_admin_profile_page_loads(self):
        response = self.client.get("/perfil/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informações da conta")
        self.assertContains(response, "Alterar palavra-passe")
        self.assertContains(response, "/static/js/admin-profile.js")


class ApiAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_cors_preflight_allows_flutter_web_origin(self):
        response = self.client.options(
            "/api/v1/auth/token/",
            HTTP_ORIGIN="http://127.0.0.1:7357",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["access-control-allow-origin"],
            "http://127.0.0.1:7357",
        )

        authenticated_response = self.client.options(
            "/api/v1/auth/me/",
            HTTP_ORIGIN="http://127.0.0.1:7357",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
        )

        self.assertEqual(authenticated_response.status_code, 200)
        self.assertIn(
            "authorization",
            authenticated_response["access-control-allow-headers"].lower(),
        )

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
        refresh_token = RefreshToken(response.data["refresh"])
        self.assertEqual(
            refresh_token["exp"] - refresh_token["iat"],
            int(timedelta(hours=1).total_seconds()),
        )

        refresh_response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 200)
        self.assertNotIn("refresh", refresh_response.data)

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

    @patch("core.api.serializers.Utilizador.objects.get")
    def test_refresh_rejects_token_older_than_session_lifetime(self, get_user):
        user = Utilizador(
            id=1,
            email="teste@example.com",
            password_hash=make_password("password-123"),
            ativo=True,
            criado_em=datetime.now(datetime_timezone.utc),
            atualizado_em=datetime.now(datetime_timezone.utc),
        )
        now = int(django_timezone.now().timestamp())
        refresh = RefreshToken.for_user(user)
        refresh["iat"] = now - int(timedelta(hours=1).total_seconds()) - 1
        refresh["exp"] = now + int(timedelta(days=6).total_seconds())

        response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        get_user.assert_not_called()

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
        Convite,
        RegistoUtilizador,
        TentativaLogin,
        TipoTrabalho,
        TemplateEtapa,
        Material,
        Encomenda,
        Trabalho,
        Ficheiro,
        TrabalhoDente,
        TrabalhoMaterial,
        EtapaTrabalho,
        RegistoEtapa,
        Nota,
        Mensagem,
        Auditoria,
        Notificacao,
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
        Notificacao.objects.all().delete()
        Auditoria.objects.all().delete()
        Mensagem.objects.all().delete()
        Nota.objects.all().delete()
        RegistoEtapa.objects.all().delete()
        EtapaTrabalho.objects.all().delete()
        Ficheiro.objects.all().delete()
        TrabalhoDente.objects.all().delete()
        TrabalhoMaterial.objects.all().delete()
        TemplateEtapa.objects.all().delete()
        TentativaLogin.objects.all().delete()
        RegistoUtilizador.objects.all().delete()
        Convite.objects.all().delete()
        PermissaoColaborador.objects.all().delete()
        Trabalho.objects.all().delete()
        Encomenda.objects.all().delete()
        Cliente.objects.all().delete()
        Colaborador.objects.all().delete()
        Administrador.objects.all().delete()
        TipoTrabalho.objects.all().delete()
        Material.objects.all().delete()
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

    def create_user(self, email, active=True):
        now = django_timezone.now()
        return Utilizador.objects.create(
            email=email,
            password_hash=make_password("test-password"),
            ativo=active,
            criado_em=now,
            atualizado_em=now,
        )

    def create_client(self, email, nif):
        user = self.create_user(email)
        client = Cliente.objects.create(
            utilizador=user,
            nome=email,
            nif=nif,
            tem_conta=True,
            ativo=True,
        )
        MedicoResponsavel.objects.create(cliente=client, nome=f"Dr. {nif}")
        return client

    def create_pending_client(self, email, nif):
        user = self.create_user(email, active=False)
        client = Cliente.objects.create(
            utilizador=user,
            nome=email,
            nif=nif,
            tem_conta=True,
            ativo=False,
        )
        MedicoResponsavel.objects.create(cliente=client, nome=f"Dr. {nif}")
        return user, client

    def create_pending_collaborator(self, email):
        user = self.create_user(email, active=False)
        collaborator = Colaborador.objects.create(
            utilizador=user,
            nome="Colaborador Pendente",
            ativo=False,
        )
        return user, collaborator

    def create_notification(self, user, title, created_at=None):
        return Notificacao.objects.create(
            utilizador=user,
            tipo="trabalho_atualizado",
            titulo=title,
            conteudo="Atualização de demonstração.",
            criada_em=created_at or django_timezone.now(),
        )

    def create_template_stage(self, name, order, active=True):
        return TemplateEtapa.objects.create(
            tipo_trabalho=self.work_type,
            nome_etapa=name,
            ordem=order,
            ativa=active,
        )

    def create_work_stage(
        self,
        work,
        template,
        name,
        order,
        state="Por Iniciar",
        active=True,
    ):
        now = django_timezone.now()
        return EtapaTrabalho.objects.create(
            trabalho=work,
            template_etapa=template,
            nome=name,
            ordem=order,
            estado=state,
            ativa=active,
            criada_em=now,
            atualizada_em=now,
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

    def test_administrator_can_view_and_update_profile(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.get("/api/v1/admin/perfil/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nome"], "Admin")
        self.assertEqual(response.data["email"], "admin@example.com")
        self.assertTrue(response.data["ativo"])

        response = self.api.patch(
            "/api/v1/admin/perfil/",
            {"nome": "Administradora", "email": "novo-admin@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nome"], "Administradora")
        self.assertEqual(response.data["email"], "novo-admin@example.com")
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.email, "novo-admin@example.com")
        self.assertEqual(self.admin.administrador.nome, "Administradora")

    def test_administrator_profile_rejects_an_email_in_use(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.patch(
            "/api/v1/admin/perfil/",
            {"email": self.collaborator.email},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.email, "admin@example.com")

    def test_administrator_can_change_password(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(
            "/api/v1/admin/perfil/alterar-palavra-passe/",
            {
                "current_password": "test-password",
                "new_password": "new-password-123",
                "confirm_password": "new-password-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(check_password("new-password-123", self.admin.password_hash))

    def test_password_change_rejects_wrong_current_password_or_confirmation(self):
        self.api.force_authenticate(user=self.admin)

        wrong_current_response = self.api.post(
            "/api/v1/admin/perfil/alterar-palavra-passe/",
            {
                "current_password": "wrong-password",
                "new_password": "new-password-123",
                "confirm_password": "new-password-123",
            },
            format="json",
        )
        mismatch_response = self.api.post(
            "/api/v1/admin/perfil/alterar-palavra-passe/",
            {
                "current_password": "test-password",
                "new_password": "new-password-123",
                "confirm_password": "different-password",
            },
            format="json",
        )
        short_password_response = self.api.post(
            "/api/v1/admin/perfil/alterar-palavra-passe/",
            {
                "current_password": "test-password",
                "new_password": "short",
                "confirm_password": "short",
            },
            format="json",
        )

        self.assertEqual(wrong_current_response.status_code, 400)
        self.assertEqual(mismatch_response.status_code, 400)
        self.assertEqual(short_password_response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(check_password("test-password", self.admin.password_hash))

    def test_only_administrators_can_manage_admin_profile(self):
        self.api.force_authenticate(user=self.collaborator)

        profile_response = self.api.get("/api/v1/admin/perfil/")
        password_response = self.api.post(
            "/api/v1/admin/perfil/alterar-palavra-passe/",
            {},
            format="json",
        )

        self.assertEqual(profile_response.status_code, 403)
        self.assertEqual(password_response.status_code, 403)

    def test_administrator_can_create_a_work_on_behalf_of_a_client(self):
        first_template = self.create_template_stage("Modelação", 1)
        second_template = self.create_template_stage("Acabamento", 2)
        self.create_template_stage("Etapa arquivada", 3, active=False)
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(
            "/api/v1/admin/trabalhos/",
            {
                "cliente": self.client_one.pk,
                "paciente_nome": "Paciente de teste",
                "tipo_trabalho": self.work_type.pk,
                "materiais": ["Dissilicato de lítio", "Resina"],
                "dentes": [11, 21],
                "data_limite": "2026-12-15",
                "observacoes": "Indicação clínica de teste.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        work = Trabalho.objects.get(pk=response.data["id"])
        order = Encomenda.objects.get(pk=work.encomenda_id)
        self.assertEqual(order.cliente_id, self.client_one.pk)
        self.assertEqual(order.criada_por_id, self.admin.pk)
        self.assertEqual(order.paciente_nome, "Paciente de teste")
        self.assertEqual(order.estado, "Aceite")
        self.assertEqual(work.estado, "Por Iniciar")
        self.assertEqual(work.data_limite.isoformat(), "2026-12-15")
        self.assertEqual(work.observacoes, "Indicação clínica de teste.")
        self.assertEqual(
            set(
                TrabalhoMaterial.objects.filter(trabalho=work)
                .values_list("material__nome", flat=True)
            ),
            {"Dissilicato de lítio", "Resina"},
        )
        self.assertEqual(
            set(
                TrabalhoDente.objects.filter(trabalho=work)
                .values_list("numero_dente", flat=True)
            ),
            {11, 21},
        )
        self.assertEqual(
            list(
                EtapaTrabalho.objects.filter(trabalho=work)
                .order_by("ordem")
                .values_list("template_etapa_id", flat=True)
            ),
            [first_template.pk, second_template.pk],
        )

    def test_work_creation_requires_admin_and_valid_teeth(self):
        payload = {
            "cliente": self.client_one.pk,
            "paciente_nome": "Paciente de teste",
            "tipo_trabalho": self.work_type.pk,
            "materiais": ["Resina"],
            "dentes": [19],
        }
        self.api.force_authenticate(user=self.collaborator)

        forbidden_response = self.api.post(
            "/api/v1/admin/trabalhos/",
            payload,
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, 403)

        self.api.force_authenticate(user=self.admin)
        invalid_response = self.api.post(
            "/api/v1/admin/trabalhos/",
            payload,
            format="json",
        )

        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(Trabalho.objects.count(), 4)
        self.assertEqual(Encomenda.objects.count(), 5)

    def test_work_creation_rolls_back_if_selected_material_is_inactive(self):
        Material.objects.create(nome="Resina inativa", ativo=False)
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(
            "/api/v1/admin/trabalhos/",
            {
                "cliente": self.client_one.pk,
                "paciente_nome": "Paciente de teste",
                "tipo_trabalho": self.work_type.pk,
                "materiais": ["Resina inativa"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Trabalho.objects.count(), 4)
        self.assertEqual(Encomenda.objects.count(), 5)

    def test_administrator_can_create_work_without_materials_and_attach_files(self):
        image = SimpleUploadedFile(
            "scan.png",
            b"fake image data",
            content_type="image/png",
        )
        document = SimpleUploadedFile(
            "prescription.pdf",
            b"fake pdf data",
            content_type="application/pdf",
        )
        self.api.force_authenticate(user=self.admin)

        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                response = self.api.post(
                    "/api/v1/admin/trabalhos/",
                    {
                        "cliente": str(self.client_one.pk),
                        "paciente_nome": "Paciente com anexos",
                        "tipo_trabalho": str(self.work_type.pk),
                        "ficheiros": [image, document],
                    },
                    format="multipart",
                )

                self.assertEqual(response.status_code, 201)
                self.assertEqual(len(response.data["ficheiros"]), 2)
                work = Trabalho.objects.get(pk=response.data["id"])
                self.assertEqual(
                    TrabalhoMaterial.objects.filter(trabalho=work).count(),
                    0,
                )
                stored_files = list(Ficheiro.objects.filter(trabalho=work).order_by("pk"))
                self.assertEqual(len(stored_files), 2)
                self.assertEqual(
                    {stored_file.nome_original for stored_file in stored_files},
                    {"scan.png", "prescription.pdf"},
                )
                self.assertTrue(
                    all(not stored_file.visivel_cliente for stored_file in stored_files)
                )
                for stored_file in stored_files:
                    self.assertTrue(
                        default_storage.exists(stored_file.chave_armazenamento)
                    )

                download_response = self.api.get(
                    f"/api/v1/admin/ficheiros/{stored_files[0].pk}/"
                )

                self.assertEqual(download_response.status_code, 200)
                self.assertIn("attachment", download_response["Content-Disposition"])
                self.assertEqual(
                    b"".join(download_response.streaming_content),
                    b"fake image data",
                )

    def test_only_administrators_can_download_work_files(self):
        stored_file = Ficheiro.objects.create(
            trabalho=self.client_work,
            enviado_por=self.admin,
            nome_original="scan.png",
            chave_armazenamento="missing/scan",
            tipo_mime="image/png",
            categoria="imagem",
            tamanho_bytes=10,
            visivel_cliente=False,
            enviado_em=django_timezone.now(),
        )
        self.api.force_authenticate(user=self.collaborator)

        response = self.api.get(f"/api/v1/admin/ficheiros/{stored_file.pk}/")

        self.assertEqual(response.status_code, 403)

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

    def test_only_administrators_can_list_clients(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.get("/api/v1/clientes/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item["id"] for item in response.data},
            {self.client_one.pk, self.client_two.pk},
        )
        self.assertEqual(
            set(response.data[0]),
            {
                "id",
                "nome",
                "medicos_responsaveis",
                "nif",
                "email_contacto",
                "telefone",
                "tem_conta",
                "ativo",
            },
        )
        self.assertEqual(
            self.api.post("/api/v1/clientes/", {}, format="json").status_code,
            400,
        )

        self.api.force_authenticate(user=self.collaborator)
        self.assertEqual(self.api.get("/api/v1/clientes/").status_code, 403)
        self.assertEqual(
            self.api.post("/api/v1/clientes/", {}, format="json").status_code,
            403,
        )
        self.api.force_authenticate(user=self.client_one.utilizador)
        self.assertEqual(self.api.get("/api/v1/clientes/").status_code, 403)

    def test_administrator_can_update_collaborator_and_password(self):
        self.api.force_authenticate(user=self.admin)
        url = f"/api/v1/colaboradores/{self.collaborator.pk}/"

        detail_response = self.api.get(url)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["email"], "tecnico@example.com")

        response = self.api.patch(
            url,
            {
                "nome": "Técnico Atualizado",
                "email": "novo.tecnico@example.com",
                "password": "password-nova-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.collaborator.refresh_from_db()
        collaborator = Colaborador.objects.get(pk=self.collaborator.pk)
        self.assertEqual(collaborator.nome, "Técnico Atualizado")
        self.assertEqual(self.collaborator.email, "novo.tecnico@example.com")
        self.assertTrue(
            check_password("password-nova-123", self.collaborator.password_hash)
        )

        self.api.force_authenticate(user=self.collaborator)
        self.assertEqual(
            self.api.patch(
                url,
                {"nome": "Alteração não autorizada"},
                format="json",
            ).status_code,
            403,
        )

    def test_client_edit_keeps_or_updates_account_password(self):
        self.api.force_authenticate(user=self.admin)
        url = f"/api/v1/clientes/{self.client_one.pk}/"

        unchanged_response = self.api.patch(
            url,
            {"nome": "Clínica com conta"},
            format="json",
        )
        self.assertEqual(unchanged_response.status_code, 200, unchanged_response.data)
        self.client_one.utilizador.refresh_from_db()
        self.assertTrue(
            check_password("test-password", self.client_one.utilizador.password_hash)
        )

        changed_response = self.api.patch(
            url,
            {"password": "nova-password-123"},
            format="json",
        )
        self.assertEqual(changed_response.status_code, 200, changed_response.data)
        self.client_one.utilizador.refresh_from_db()
        self.assertTrue(
            check_password("nova-password-123", self.client_one.utilizador.password_hash)
        )
        self.assertNotIn("password", changed_response.data)

    def test_editing_client_without_account_creates_account(self):
        self.api.force_authenticate(user=self.admin)
        client = Cliente.objects.create(
            criado_por_admin=self.admin,
            nome="Clínica sem conta",
            nif="444444444",
            email_contacto="sem.conta@example.com",
            tem_conta=False,
            ativo=True,
        )
        MedicoResponsavel.objects.create(cliente=client, nome="Dra. Exemplo")

        response = self.api.patch(
            f"/api/v1/clientes/{client.pk}/",
            {
                "email_contacto": "nova.conta@example.com",
                "password": "password-nova-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        client.refresh_from_db()
        self.assertTrue(client.tem_conta)
        self.assertEqual(client.utilizador.email, "nova.conta@example.com")
        self.assertTrue(
            check_password("password-nova-123", client.utilizador.password_hash)
        )

    def test_administrator_can_update_client_and_responsible_doctors(self):
        self.api.force_authenticate(user=self.admin)
        initial_detail = self.api.get(
            f"/api/v1/clientes/{self.client_one.pk}/"
        )
        self.assertEqual(
            initial_detail.data["email_contacto"],
            "cliente1@example.com",
        )

        response = self.api.patch(
            f"/api/v1/clientes/{self.client_one.pk}/",
            {
                "nome": "Clínica Atualizada",
                "email_contacto": "novo@example.com",
                "telefone": "912345678",
                "morada": "Rua Nova, 10",
                "medicos_responsaveis": ["Dra. Nova", "Dr. Atualizado"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.client_one.refresh_from_db()
        self.assertEqual(self.client_one.nome, "Clínica Atualizada")
        self.assertEqual(self.client_one.email_contacto, "novo@example.com")
        self.assertEqual(self.client_one.utilizador.email, "novo@example.com")
        self.assertEqual(self.client_one.telefone, "912345678")
        self.assertEqual(self.client_one.morada, "Rua Nova, 10")
        self.assertCountEqual(
            response.data["medicos_responsaveis"],
            ["Dra. Nova", "Dr. Atualizado"],
        )
        self.assertCountEqual(
            MedicoResponsavel.objects.filter(cliente=self.client_one)
            .values_list("nome", flat=True),
            ["Dra. Nova", "Dr. Atualizado"],
        )

        detail_response = self.api.get(
            f"/api/v1/clientes/{self.client_one.pk}/"
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data["morada"], "Rua Nova, 10")

        self.api.force_authenticate(user=self.collaborator)
        self.assertEqual(
            self.api.patch(
                f"/api/v1/clientes/{self.client_one.pk}/",
                {"nome": "Alteração não autorizada"},
                format="json",
            ).status_code,
            403,
        )

    def test_client_api_rejects_nif_and_phone_without_nine_digits(self):
        self.api.force_authenticate(user=self.admin)
        url = f"/api/v1/clientes/{self.client_one.pk}/"

        invalid_payloads = (
            {"nif": "12345678"},
            {"nif": "12345678A"},
            {"telefone": "12345678"},
            {"telefone": "12345678A"},
            {"telefone": "123 456 789"},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.api.patch(url, payload, format="json")
                self.assertEqual(response.status_code, 400, response.data)

    def test_client_creation_rejects_invalid_client_data(self):
        self.api.force_authenticate(user=self.admin)

        invalid_payloads = (
            {
                "nome": "Clínica NIF inválido",
                "nif": "12345678A",
                "email_contacto": "nif-invalid@example.com",
                "password": "client-password-123",
                "medicos_responsaveis": ["Dra. Teste"],
            },
            {
                "nome": "Clínica telefone inválido",
                "nif": "333333333",
                "email_contacto": "phone-invalid@example.com",
                "password": "client-password-123",
                "telefone": "12345678A",
                "medicos_responsaveis": ["Dra. Teste"],
            },
            {
                "nome": "Clínica sem password",
                "nif": "333333334",
                "email_contacto": "no-password@example.com",
                "password": "short",
                "medicos_responsaveis": ["Dra. Teste"],
            },
            {
                "nome": "Clínica com e-mail ocupado",
                "nif": "333333335",
                "email_contacto": self.admin.email,
                "password": "client-password-123",
                "medicos_responsaveis": ["Dra. Teste"],
            },
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.api.post(
                    "/api/v1/clientes/",
                    payload,
                    format="json",
                )
                self.assertEqual(response.status_code, 400, response.data)

    def test_administrator_can_create_client_with_hashed_account(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(
            "/api/v1/clientes/",
            {
                "nome": "Clínica Exemplo",
                "nif": "987654321",
                "email_contacto": "contacto@exemplo.pt",
                "password": "cliente-password-123",
                "telefone": "912345678",
                "morada": "Rua de Exemplo, 1",
                "medicos_responsaveis": ["Dra. Ana Rodrigues", "Dr. João Silva"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        client = Cliente.objects.get(nif="987654321")
        self.assertEqual(client.nome, "Clínica Exemplo")
        self.assertIsNotNone(client.utilizador_id)
        self.assertEqual(client.criado_por_admin_id, self.admin.pk)
        self.assertTrue(client.tem_conta)
        self.assertTrue(client.ativo)
        self.assertEqual(client.utilizador.email, "contacto@exemplo.pt")
        self.assertTrue(client.utilizador.ativo)
        self.assertTrue(
            check_password("cliente-password-123", client.utilizador.password_hash)
        )
        self.assertNotIn("password", response.data)
        self.api.force_authenticate(user=None)
        login_response = self.api.post(
            "/api/v1/auth/token/",
            {
                "email": "contacto@exemplo.pt",
                "password": "cliente-password-123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, 200, login_response.data)
        profile_response = self.api.get(
            "/api/v1/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}",
        )
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data["perfil"], "cliente")
        self.api.force_authenticate(user=self.admin)
        self.assertCountEqual(
            list(
                MedicoResponsavel.objects.filter(cliente=client)
                .order_by("nome")
                .values_list("nome", flat=True)
            ),
            ["Dr. João Silva", "Dra. Ana Rodrigues"],
        )
        self.assertCountEqual(
            response.data["medicos_responsaveis"],
            ["Dra. Ana Rodrigues", "Dr. João Silva"],
        )

        duplicate_response = self.api.post(
            "/api/v1/clientes/",
            {
                "nome": "Cliente duplicado",
                "nif": "987654321",
                "email_contacto": "duplicado@example.pt",
                "password": "cliente-password-123",
                "medicos_responsaveis": ["Dr. Outro Médico"],
            },
            format="json",
        )
        self.assertEqual(duplicate_response.status_code, 400)

    def test_administrator_must_add_at_least_one_responsible_doctor(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(
            "/api/v1/clientes/",
            {
                "nome": "Clínica sem médico",
                "nif": "123456789",
                "medicos_responsaveis": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("medicos_responsaveis", response.data)

    def test_only_administrators_can_list_collaborators_and_permissions(self):
        PermissaoColaborador.objects.create(
            colaborador_id=self.collaborator.pk,
            codigo=PermissaoColaborador.Codigo.RECECAO_TRABALHOS,
            concedida_por=self.admin,
        )
        self.api.force_authenticate(user=self.admin)

        response = self.api.get("/api/v1/colaboradores/")

        self.assertEqual(response.status_code, 200)
        collaborator_data = next(
            item for item in response.data if item["id"] == self.collaborator.pk
        )
        self.assertEqual(collaborator_data["email"], self.collaborator.email)
        self.assertEqual(
            collaborator_data["permissoes"],
            [PermissaoColaborador.Codigo.RECECAO_TRABALHOS],
        )
        self.assertEqual(
            self.api.post("/api/v1/colaboradores/", {}, format="json").status_code,
            405,
        )

        self.api.force_authenticate(user=self.collaborator)
        self.assertEqual(self.api.get("/api/v1/colaboradores/").status_code, 403)

        self.api.force_authenticate(user=self.client_one.utilizador)
        self.assertEqual(self.api.get("/api/v1/colaboradores/").status_code, 403)

    def test_administrator_can_list_pending_clients_and_collaborators(self):
        client_user, _ = self.create_pending_client(
            "pendente-cliente@example.com",
            "333333333",
        )
        collaborator_user, _ = self.create_pending_collaborator(
            "pendente-colaborador@example.com"
        )
        self.api.force_authenticate(user=self.admin)

        response = self.api.get("/api/v1/utilizadores/pendentes/")

        self.assertEqual(response.status_code, 200)
        pending = {item["id"]: item for item in response.data}
        self.assertEqual(set(pending), {client_user.pk, collaborator_user.pk})
        self.assertEqual(pending[client_user.pk]["perfil"], "Cliente")
        self.assertEqual(pending[client_user.pk]["nome"], client_user.email)
        self.assertEqual(
            pending[collaborator_user.pk]["perfil"],
            "Colaborador",
        )
        self.assertEqual(
            set(pending[client_user.pk]),
            {"id", "email", "nome", "perfil", "criado_em"},
        )

        self.api.force_authenticate(user=self.collaborator)
        self.assertEqual(self.api.get("/api/v1/utilizadores/pendentes/").status_code, 403)

    def test_users_only_receive_their_own_notifications(self):
        admin_notification = self.create_notification(
            self.admin,
            "Notificação do administrador",
        )
        client_notification = self.create_notification(
            self.client_one.utilizador,
            "Notificação do cliente",
        )
        self.create_notification(self.collaborator, "Notificação do colaborador")

        self.api.force_authenticate(user=self.admin)
        admin_response = self.api.get("/api/v1/notificacoes/")
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in admin_response.data],
            [admin_notification.pk],
        )
        self.assertEqual(
            set(admin_response.data[0]),
            {
                "id",
                "tipo",
                "titulo",
                "conteudo",
                "trabalho",
                "criada_em",
                "lida_em",
            },
        )

        self.api.force_authenticate(user=self.client_one.utilizador)
        client_response = self.api.get("/api/v1/notificacoes/")
        self.assertEqual(client_response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in client_response.data],
            [client_notification.pk],
        )

    def test_users_can_mark_only_their_own_notifications_as_read(self):
        own_notification = self.create_notification(
            self.admin,
            "Notificação própria",
        )
        other_notification = self.create_notification(
            self.client_one.utilizador,
            "Notificação de outro utilizador",
        )
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(
            f"/api/v1/notificacoes/{own_notification.pk}/ler/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["lida_em"])
        own_notification.refresh_from_db()
        self.assertIsNotNone(own_notification.lida_em)
        repeated_response = self.api.post(
            f"/api/v1/notificacoes/{own_notification.pk}/ler/"
        )
        self.assertEqual(repeated_response.status_code, 200)
        self.assertEqual(
            repeated_response.data["lida_em"],
            response.data["lida_em"],
        )
        self.assertEqual(
            self.api.post(
                f"/api/v1/notificacoes/{other_notification.pk}/ler/"
            ).status_code,
            404,
        )

    def test_stage_templates_are_only_available_to_administrators(self):
        self.api.force_authenticate(user=self.admin)

        type_response = self.api.get("/api/v1/tipos-trabalho/")
        stages_response = self.api.get(
            f"/api/v1/tipos-trabalho/{self.work_type.pk}/etapas/"
        )

        self.assertEqual(type_response.status_code, 200)
        self.assertEqual(type_response.data[0]["nome"], self.work_type.nome)
        self.assertEqual(stages_response.status_code, 200)
        self.assertEqual(stages_response.data, [])

        self.api.force_authenticate(user=self.collaborator)
        self.assertEqual(self.api.get("/api/v1/tipos-trabalho/").status_code, 403)
        self.assertEqual(
            self.api.get(
                f"/api/v1/tipos-trabalho/{self.work_type.pk}/etapas/"
            ).status_code,
            403,
        )

    def test_adding_stage_adds_it_to_open_works_of_that_type(self):
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(
            f"/api/v1/tipos-trabalho/{self.work_type.pk}/etapas/",
            {"nome_etapa": "Polimento"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        template = TemplateEtapa.objects.get(pk=response.data["id"])
        self.assertEqual(template.ordem, 1)
        self.assertTrue(template.ativa)
        stages = EtapaTrabalho.objects.filter(template_etapa=template)
        self.assertEqual(
            set(stages.values_list("trabalho_id", flat=True)),
            {
                self.client_work.pk,
                self.other_client_work.pk,
                self.review_work.pk,
            },
        )
        self.assertTrue(
            all(stage.estado == "Por Iniciar" and stage.ativa for stage in stages)
        )
        self.assertFalse(
            EtapaTrabalho.objects.filter(
                template_etapa=template,
                trabalho=self.completed_work,
            ).exists()
        )

    def test_stage_edits_propagate_only_to_open_work_and_preserve_progress(self):
        template = self.create_template_stage("Acabamento", 1)
        open_stage = self.create_work_stage(
            self.client_work,
            template,
            "Acabamento",
            1,
            state="Em Processamento",
        )
        completed_stage = self.create_work_stage(
            self.completed_work,
            template,
            "Acabamento",
            1,
            state="Concluído",
        )
        old_open_updated_at = open_stage.atualizada_em
        self.api.force_authenticate(user=self.admin)

        response = self.api.patch(
            f"/api/v1/etapas-template/{template.pk}/",
            {"nome_etapa": "Polimento final", "ativa": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        open_stage.refresh_from_db()
        completed_stage.refresh_from_db()
        self.assertEqual(open_stage.nome, "Polimento final")
        self.assertFalse(open_stage.ativa)
        self.assertEqual(open_stage.estado, "Em Processamento")
        self.assertGreater(open_stage.atualizada_em, old_open_updated_at)
        self.assertEqual(completed_stage.nome, "Acabamento")
        self.assertTrue(completed_stage.ativa)
        self.assertEqual(completed_stage.estado, "Concluído")

    def test_reordering_template_updates_open_work_order_only(self):
        first_template = self.create_template_stage("Moldagem", 1)
        second_template = self.create_template_stage("Acabamento", 2)
        open_first = self.create_work_stage(
            self.client_work,
            first_template,
            "Moldagem",
            1,
        )
        open_second = self.create_work_stage(
            self.client_work,
            second_template,
            "Acabamento",
            2,
        )
        completed_first = self.create_work_stage(
            self.completed_work,
            first_template,
            "Moldagem",
            1,
        )
        completed_second = self.create_work_stage(
            self.completed_work,
            second_template,
            "Acabamento",
            2,
        )
        self.api.force_authenticate(user=self.admin)

        response = self.api.patch(
            f"/api/v1/etapas-template/{second_template.pk}/",
            {"ordem": 1},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        first_template.refresh_from_db()
        second_template.refresh_from_db()
        open_first.refresh_from_db()
        open_second.refresh_from_db()
        completed_first.refresh_from_db()
        completed_second.refresh_from_db()
        self.assertEqual((second_template.ordem, first_template.ordem), (1, 2))
        self.assertEqual((open_second.ordem, open_first.ordem), (1, 2))
        self.assertEqual((completed_first.ordem, completed_second.ordem), (1, 2))

    def test_administrator_approval_activates_user_and_profile(self):
        client_user, client_profile = self.create_pending_client(
            "aprovar-cliente@example.com",
            "444444444",
        )
        collaborator_user, collaborator_profile = self.create_pending_collaborator(
            "aprovar-colaborador@example.com"
        )
        self.api.force_authenticate(user=self.admin)

        client_response = self.api.post(
            f"/api/v1/utilizadores/{client_user.pk}/aprovar/"
        )
        collaborator_response = self.api.post(
            f"/api/v1/utilizadores/{collaborator_user.pk}/aprovar/"
        )

        self.assertEqual(client_response.status_code, 200)
        self.assertEqual(collaborator_response.status_code, 200)
        client_user.refresh_from_db()
        client_profile.refresh_from_db()
        collaborator_user.refresh_from_db()
        collaborator_profile.refresh_from_db()
        self.assertTrue(client_user.ativo)
        self.assertTrue(client_profile.ativo)
        self.assertTrue(collaborator_user.ativo)
        self.assertTrue(collaborator_profile.ativo)

    def test_rejecting_pending_client_removes_request_and_preserves_audit_records(self):
        user, profile = self.create_pending_client(
            "rejeitar-cliente@example.com",
            "555555555",
        )
        now = django_timezone.now()
        registration = RegistoUtilizador.objects.create(
            utilizador=user,
            criado_em=now,
        )
        login_attempt = TentativaLogin.objects.create(
            utilizador=user,
            email_tentado=user.email,
            sucesso=False,
            tentada_em=now,
        )
        audit = Auditoria.objects.create(
            utilizador=user,
            entidade="utilizador",
            entidade_id=user.pk,
            acao="registo",
            data_hora=now,
        )
        self.api.force_authenticate(user=self.admin)

        response = self.api.delete(
            f"/api/v1/utilizadores/{user.pk}/rejeitar/"
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Utilizador.objects.filter(pk=user.pk).exists())
        self.assertFalse(Cliente.objects.filter(pk=profile.pk).exists())
        self.assertFalse(RegistoUtilizador.objects.filter(pk=registration.pk).exists())
        login_attempt.refresh_from_db()
        audit.refresh_from_db()
        self.assertIsNone(login_attempt.utilizador)
        self.assertIsNone(audit.utilizador)

    def test_rejecting_pending_client_with_orders_keeps_account_intact(self):
        user, profile = self.create_pending_client(
            "com-trabalho@example.com",
            "666666666",
        )
        Encomenda.objects.create(
            cliente=profile,
            criada_por=self.admin,
            paciente_nome="Paciente",
            estado="Aceite",
            data_criacao=django_timezone.now(),
        )
        self.api.force_authenticate(user=self.admin)

        response = self.api.delete(
            f"/api/v1/utilizadores/{user.pk}/rejeitar/"
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Utilizador.objects.filter(pk=user.pk, ativo=False).exists())
        self.assertTrue(Cliente.objects.filter(pk=profile.pk, ativo=False).exists())

    def test_account_without_inactive_profile_cannot_be_approved(self):
        user = self.create_user("sem-perfil-pendente@example.com", active=False)
        self.api.force_authenticate(user=self.admin)

        response = self.api.post(f"/api/v1/utilizadores/{user.pk}/aprovar/")

        self.assertEqual(response.status_code, 404)
        user.refresh_from_db()
        self.assertFalse(user.ativo)

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
