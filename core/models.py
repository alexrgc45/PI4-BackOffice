# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Administrador(models.Model):
    utilizador = models.OneToOneField('Utilizador', models.DO_NOTHING, primary_key=True)
    nome = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'administrador'


class Auditoria(models.Model):
    utilizador = models.ForeignKey('Utilizador', models.DO_NOTHING, blank=True, null=True)
    trabalho = models.ForeignKey('Trabalho', models.DO_NOTHING, blank=True, null=True)
    origem = models.CharField(max_length=100, blank=True, null=True)
    entidade = models.CharField(max_length=100)
    entidade_id = models.IntegerField()
    acao = models.CharField(max_length=50)
    detalhes = models.JSONField(blank=True, null=True)
    data_hora = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auditoria'


class Cliente(models.Model):
    utilizador = models.OneToOneField('Utilizador', models.DO_NOTHING, blank=True, null=True)
    criado_por_admin = models.ForeignKey('Utilizador', models.DO_NOTHING, db_column='criado_por_admin', related_name='cliente_criado_por_admin_set', blank=True, null=True)
    nome = models.CharField(max_length=255)
    idade = models.IntegerField(blank=True, null=True)
    nif = models.CharField(unique=True, max_length=20)
    email_contacto = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=50, blank=True, null=True)
    morada = models.TextField(blank=True, null=True)
    tem_conta = models.BooleanField()
    ativo = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'cliente'


class MedicoResponsavel(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        models.CASCADE,
        related_name='medicos_responsaveis',
    )
    nome = models.CharField(max_length=255)

    class Meta:
        db_table = 'medico_responsavel'
        ordering = ('nome', 'pk')


class Colaborador(models.Model):
    utilizador = models.OneToOneField('Utilizador', models.DO_NOTHING, primary_key=True)
    nome = models.CharField(max_length=255)
    ativo = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'colaborador'


class Convite(models.Model):
    email = models.CharField(max_length=255)
    token_hash = models.CharField(unique=True, max_length=255)
    perfil = models.CharField(max_length=50)
    cliente = models.ForeignKey(Cliente, models.DO_NOTHING, blank=True, null=True)
    criado_por = models.ForeignKey('Utilizador', models.DO_NOTHING, db_column='criado_por', blank=True, null=True)
    criado_em = models.DateTimeField()
    expira_em = models.DateTimeField()
    usado_em = models.DateTimeField(blank=True, null=True)
    utilizador_criado = models.ForeignKey('Utilizador', models.DO_NOTHING, related_name='convite_utilizador_criado_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'convite'


class Encomenda(models.Model):
    cliente = models.ForeignKey(Cliente, models.DO_NOTHING)
    criada_por = models.ForeignKey('Utilizador', models.DO_NOTHING, db_column='criada_por')
    aceite_por = models.ForeignKey('Utilizador', models.DO_NOTHING, db_column='aceite_por', related_name='encomenda_aceite_por_set', blank=True, null=True)
    paciente_nome = models.CharField(max_length=255)
    paciente_idade = models.IntegerField(blank=True, null=True)
    paciente_sexo = models.CharField(max_length=20, blank=True, null=True)
    estado = models.CharField(max_length=50)
    data_criacao = models.DateTimeField()
    data_aceitacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'encomenda'


class EtapaTrabalho(models.Model):
    trabalho = models.ForeignKey('Trabalho', models.DO_NOTHING)
    template_etapa = models.ForeignKey('TemplateEtapa', models.DO_NOTHING, blank=True, null=True)
    nome = models.CharField(max_length=150)
    ordem = models.IntegerField()
    estado = models.CharField(max_length=50)
    ativa = models.BooleanField()
    criada_em = models.DateTimeField()
    atualizada_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'etapa_trabalho'


class Ficheiro(models.Model):
    trabalho = models.ForeignKey('Trabalho', models.DO_NOTHING)
    enviado_por = models.ForeignKey('Utilizador', models.DO_NOTHING, db_column='enviado_por')
    nome_original = models.CharField(max_length=255)
    chave_armazenamento = models.CharField(unique=True, max_length=255)
    tipo_mime = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.CharField(max_length=50)
    tamanho_bytes = models.BigIntegerField(blank=True, null=True)
    visivel_cliente = models.BooleanField()
    enviado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'ficheiro'


class Material(models.Model):
    nome = models.CharField(unique=True, max_length=150)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'material'


class MaterialAEnviar(models.Model):
    trabalho = models.ForeignKey('Trabalho', models.DO_NOTHING)
    descricao = models.CharField(max_length=255)
    data_prevista_envio = models.DateField(blank=True, null=True)
    data_rececao = models.DateTimeField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'material_a_enviar'


class Mensagem(models.Model):
    remetente = models.ForeignKey('Utilizador', models.DO_NOTHING)
    destinatario = models.ForeignKey('Utilizador', models.DO_NOTHING, related_name='mensagem_destinatario_set')
    trabalho = models.ForeignKey('Trabalho', models.DO_NOTHING, blank=True, null=True)
    conteudo = models.TextField()
    enviada_em = models.DateTimeField()
    lida_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mensagem'


class Nota(models.Model):
    trabalho = models.ForeignKey('Trabalho', models.DO_NOTHING)
    autor = models.ForeignKey('Utilizador', models.DO_NOTHING)
    conteudo = models.TextField()
    visivel_cliente = models.BooleanField()
    criada_em = models.DateTimeField()
    atualizada_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'nota'


class Notificacao(models.Model):
    utilizador = models.ForeignKey('Utilizador', models.DO_NOTHING)
    trabalho = models.ForeignKey('Trabalho', models.DO_NOTHING, blank=True, null=True)
    nota = models.ForeignKey(Nota, models.DO_NOTHING, blank=True, null=True)
    mensagem = models.ForeignKey(Mensagem, models.DO_NOTHING, blank=True, null=True)
    registo_etapa = models.ForeignKey('RegistoEtapa', models.DO_NOTHING, blank=True, null=True)
    tipo = models.CharField(max_length=50)
    titulo = models.CharField(max_length=255)
    conteudo = models.TextField(blank=True, null=True)
    criada_em = models.DateTimeField()
    lida_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notificacao'


class RegistoEtapa(models.Model):
    etapa_trabalho = models.ForeignKey(EtapaTrabalho, models.DO_NOTHING)
    colaborador = models.ForeignKey(Colaborador, models.DO_NOTHING)
    encaminhado_para = models.ForeignKey(Colaborador, models.DO_NOTHING, db_column='encaminhado_para', related_name='registoetapa_encaminhado_para_set', blank=True, null=True)
    nome_etapa_snapshot = models.CharField(max_length=150)
    resultado = models.CharField(max_length=50)
    justificacao_standby = models.TextField(blank=True, null=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'registo_etapa'


class RegistoUtilizador(models.Model):
    utilizador = models.ForeignKey('Utilizador', models.DO_NOTHING)
    convite = models.ForeignKey(Convite, models.DO_NOTHING, blank=True, null=True)
    ip_origem = models.CharField(max_length=45, blank=True, null=True)
    criado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'registo_utilizador'


class TemplateEtapa(models.Model):
    tipo_trabalho = models.ForeignKey('TipoTrabalho', models.DO_NOTHING)
    nome_etapa = models.CharField(max_length=150)
    ordem = models.IntegerField()
    ativa = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'template_etapa'


class TentativaLogin(models.Model):
    utilizador = models.ForeignKey('Utilizador', models.DO_NOTHING, blank=True, null=True)
    email_tentado = models.CharField(max_length=255)
    sucesso = models.BooleanField()
    motivo_falha = models.CharField(max_length=100, blank=True, null=True)
    ip_origem = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    tentada_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'tentativa_login'


class TipoTrabalho(models.Model):
    nome = models.CharField(unique=True, max_length=150)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'tipo_trabalho'


class Trabalho(models.Model):
    encomenda = models.ForeignKey(Encomenda, models.DO_NOTHING)
    tipo_trabalho = models.ForeignKey(TipoTrabalho, models.DO_NOTHING)
    natureza = models.CharField(max_length=100)
    estado = models.CharField(max_length=50)
    justificacao_standby = models.TextField(blank=True, null=True)
    cor = models.CharField(max_length=50, blank=True, null=True)
    data_limite = models.DateField(blank=True, null=True)
    data_proxima_consulta = models.DateField(blank=True, null=True)
    data_finalizacao = models.DateTimeField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField()
    atualizado_em = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'trabalho'


class TrabalhoDente(models.Model):
    pk = models.CompositePrimaryKey('trabalho_id', 'numero_dente')
    trabalho = models.ForeignKey(Trabalho, models.DO_NOTHING)
    numero_dente = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'trabalho_dente'


class TrabalhoMaterial(models.Model):
    pk = models.CompositePrimaryKey('trabalho_id', 'material_id')
    trabalho = models.ForeignKey(Trabalho, models.DO_NOTHING)
    material = models.ForeignKey(Material, models.DO_NOTHING)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trabalho_material'


class Utilizador(models.Model):
    email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    ativo = models.BooleanField()
    criado_em = models.DateTimeField()
    atualizado_em = models.DateTimeField()

    @property
    def is_authenticated(self):
        return True

    class Meta:
        managed = False
        db_table = 'utilizador'


class PermissaoColaborador(models.Model):
    class Codigo(models.TextChoices):
        RECECAO_TRABALHOS = "rececao_trabalhos", "Receção de trabalhos"

    colaborador = models.ForeignKey(
        Colaborador,
        models.DO_NOTHING,
        related_name="permissoes",
    )
    codigo = models.CharField(max_length=50, choices=Codigo.choices)
    concedida_por = models.ForeignKey(
        Utilizador,
        models.DO_NOTHING,
        related_name="permissoes_colaborador_concedidas",
    )
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "permissao_colaborador"
        constraints = [
            models.UniqueConstraint(
                fields=("colaborador", "codigo"),
                name="uq_perm_colaborador_codigo",
            ),
        ]
