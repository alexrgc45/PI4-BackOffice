import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'auth_api.dart';

/// Converte um valor vindo do JSON numa data (ou null se vier vazio/inválido).
DateTime? _lerData(Object? valor) {
  if (valor is! String || valor.isEmpty) {
    return null;
  }
  return DateTime.tryParse(valor);
}

/// Lê um inteiro que pode vir como int ou como texto (ex.: "12").
/// Se vier um objeto (ex.: {"id": 12, ...}), usa o seu "id".
int? _lerInteiro(Object? valor) {
  if (valor is int) {
    return valor;
  }
  if (valor is String) {
    return int.tryParse(valor);
  }
  if (valor is Map) {
    return _lerInteiro(valor['id']);
  }
  return null;
}

/// Lê um texto sem rebentar se a API mandar outro tipo.
/// Um `json['x'] as String?` lançaria TypeError se viesse um número;
/// aqui números passam a texto e tudo o resto (null, listas…) fica null.
String? _lerTexto(Object? valor) {
  if (valor is String) {
    return valor.trim().isEmpty ? null : valor;
  }
  if (valor is num || valor is bool) {
    return valor.toString();
  }
  return null;
}

/// Um trabalho (pedido) do cliente, tal como devolvido por GET trabalhos/.
///
/// Nota: o campo `data_limite` vem da API mas NÃO é guardado no modelo,
/// porque é uma data interna do laboratório que o cliente não deve ver.
class Trabalho {
  const Trabalho({
    required this.id,
    required this.encomenda,
    required this.pacienteNome,
    required this.tipoTrabalhoNome,
    required this.natureza,
    required this.estado,
    required this.dataProximaConsulta,
    required this.dataFinalizacao,
  });

  final int id;
  final String? encomenda;
  final String pacienteNome;
  final String tipoTrabalhoNome;
  final String? natureza;
  final String estado;
  final DateTime? dataProximaConsulta;
  final DateTime? dataFinalizacao;

  factory Trabalho.fromJson(Map<String, dynamic> json) {
    final id = _lerInteiro(json['id']);
    if (id == null) {
      throw const AuthApiException('A API devolveu um trabalho inválido.');
    }
    return Trabalho(
      id: id,
      encomenda: _lerTexto(json['encomenda']),
      pacienteNome: _lerTexto(json['paciente_nome']) ?? 'Paciente sem nome',
      tipoTrabalhoNome: _lerTexto(json['tipo_trabalho_nome']) ?? '—',
      natureza: _lerTexto(json['natureza']),
      estado: _lerTexto(json['estado']) ?? 'desconhecido',
      dataProximaConsulta: _lerData(json['data_proxima_consulta']),
      dataFinalizacao: _lerData(json['data_finalizacao']),
    );
  }
}

/// Uma notificação do cliente, tal como devolvida por GET notificacoes/.
class Notificacao {
  const Notificacao({
    required this.id,
    required this.tipo,
    required this.titulo,
    required this.conteudo,
    required this.trabalhoId,
    required this.criadaEm,
    required this.lidaEm,
  });

  final int id;
  final String? tipo;
  final String titulo;
  final String conteudo;
  final int? trabalhoId;
  final DateTime? criadaEm;
  final DateTime? lidaEm;

  /// Uma notificação está lida quando a API já tem data em `lida_em`.
  bool get lida => lidaEm != null;

  /// Devolve uma cópia desta notificação marcada como lida agora.
  /// Usado para atualizar o ecrã sem voltar a pedir a lista à API.
  Notificacao marcadaComoLida() {
    return Notificacao(
      id: id,
      tipo: tipo,
      titulo: titulo,
      conteudo: conteudo,
      trabalhoId: trabalhoId,
      criadaEm: criadaEm,
      lidaEm: lidaEm ?? DateTime.now(),
    );
  }

  factory Notificacao.fromJson(Map<String, dynamic> json) {
    final id = _lerInteiro(json['id']);
    if (id == null) {
      throw const AuthApiException('A API devolveu uma notificação inválida.');
    }
    return Notificacao(
      id: id,
      tipo: _lerTexto(json['tipo']),
      titulo: _lerTexto(json['titulo']) ?? 'Notificação',
      conteudo: _lerTexto(json['conteudo']) ?? '',
      trabalhoId: _lerInteiro(json['trabalho']),
      criadaEm: _lerData(json['criada_em']),
      lidaEm: _lerData(json['lida_em']),
    );
  }
}

/// Serviço que fala com os endpoints do cliente na API Django.
///
/// Segue o mesmo padrão do [AuthApi]: mesmo URL base (API_BASE_URL),
/// timeout de 15 s e erros lançados como [AuthApiException].
class ClienteApi {
  ClienteApi({http.Client? client, Uri? baseUri})
    : _client = client ?? http.Client(),
      _baseUri = _withTrailingSlash(
        baseUri ??
            Uri.parse(
              const String.fromEnvironment(
                'API_BASE_URL',
                defaultValue: 'http://127.0.0.1:8000/api/v1/',
              ),
            ),
      );

  static final ClienteApi instance = ClienteApi();

  static const _requestTimeout = Duration(seconds: 15);

  final http.Client _client;
  final Uri _baseUri;

  // ---------------------------------------------------------------------------
  // Métodos públicos
  // ---------------------------------------------------------------------------

  /// GET trabalhos/ — todos os trabalhos do cliente autenticado.
  Future<List<Trabalho>> listarTrabalhos() async {
    final itens = await _obterLista(_endpoint('trabalhos/'));
    return itens.map(Trabalho.fromJson).toList();
  }

  /// GET trabalhos/{id}/ — detalhe de um trabalho.
  Future<Trabalho> obterTrabalho(int id) async {
    final response = await _send(
      _client.get(_endpoint('trabalhos/$id/'), headers: _headers()),
    );
    return Trabalho.fromJson(_lerObjeto(response));
  }

  /// GET notificacoes/ — notificações do cliente autenticado.
  Future<List<Notificacao>> listarNotificacoes() async {
    final itens = await _obterLista(_endpoint('notificacoes/'));
    return itens.map(Notificacao.fromJson).toList();
  }

  /// POST notificacoes/{id}/ler/ — marca a notificação como lida.
  Future<void> marcarNotificacaoLida(int id) async {
    final response = await _send(
      _client.post(_endpoint('notificacoes/$id/ler/'), headers: _headers()),
    );
    _verificarEstado(response);
  }

  // ---------------------------------------------------------------------------
  // Auxiliares internos
  // ---------------------------------------------------------------------------

  Uri _endpoint(String path) => _baseUri.resolve(path);

  /// Cabeçalhos com o token da sessão (`Authorization: Bearer <token>`).
  Map<String, String> _headers() {
    final session = AuthApi.currentSession;
    if (session == null) {
      throw const AuthApiException(
        'Sessão terminada. Inicia sessão novamente.',
      );
    }
    return {
      'Authorization': 'Bearer ${session.accessToken}',
      'Accept': 'application/json',
    };
  }

  /// Lê uma lista da API. Aceita os dois formatos possíveis:
  /// - lista simples: `[ {...}, {...} ]`
  /// - paginada (Django REST): `{"results": [...], "next": "url"}`
  /// Se for paginada, segue o `next` até ler todas as páginas.
  Future<List<Map<String, dynamic>>> _obterLista(Uri primeiraPagina) async {
    final resultado = <Map<String, dynamic>>[];
    Uri? pagina = primeiraPagina;

    while (pagina != null) {
      final response = await _send(_client.get(pagina, headers: _headers()));
      final decoded = _descodificar(response);

      final Object? itens;
      if (decoded is List) {
        itens = decoded;
        pagina = null;
      } else if (decoded is Map<String, dynamic> &&
          decoded['results'] is List) {
        itens = decoded['results'];
        final next = decoded['next'];
        // O Django costuma mandar o URL completo da página seguinte;
        // resolve() funciona tanto com URL completo como relativo.
        pagina = next is String && next.isNotEmpty
            ? _baseUri.resolve(next)
            : null;
      } else {
        throw const AuthApiException('A API devolveu uma resposta inválida.');
      }

      for (final item in itens as List) {
        if (item is! Map<String, dynamic>) {
          throw const AuthApiException('A API devolveu uma resposta inválida.');
        }
        resultado.add(item);
      }
    }
    return resultado;
  }

  /// Igual ao `_send` do AuthApi: aplica o timeout e traduz erros de rede.
  Future<http.Response> _send(Future<http.Response> request) async {
    try {
      return await request.timeout(_requestTimeout);
    } on TimeoutException {
      throw const AuthApiException('A ligação à API excedeu o tempo limite.');
    } on http.ClientException {
      throw const AuthApiException(
        'Não foi possível contactar a API. Confirma se o backend está ativo.',
      );
    } on Exception {
      // Qualquer outra falha de rede também chega ao ecrã como mensagem
      // clara (com "Tentar de novo"), em vez de uma exceção por apanhar.
      throw const AuthApiException(
        'Ocorreu um erro inesperado ao contactar a API.',
      );
    }
  }

  /// Valida o código HTTP e descodifica o JSON da resposta.
  Object? _descodificar(http.Response response) {
    _verificarEstado(response);
    try {
      return jsonDecode(utf8.decode(response.bodyBytes));
    } on FormatException {
      throw const AuthApiException('A API devolveu uma resposta inválida.');
    }
  }

  Map<String, dynamic> _lerObjeto(http.Response response) {
    final decoded = _descodificar(response);
    if (decoded is! Map<String, dynamic>) {
      throw const AuthApiException('A API devolveu uma resposta inválida.');
    }
    return decoded;
  }

  /// Lança [AuthApiException] se o código HTTP não for 2xx,
  /// usando a mensagem `detail` do Django quando existir.
  void _verificarEstado(http.Response response) {
    final status = response.statusCode;
    if (status >= 200 && status < 300) {
      return;
    }
    // 401 = token inválido/expirado: a mesma mensagem de quando não há sessão.
    if (status == 401) {
      throw const AuthApiException(
        'Sessão terminada. Inicia sessão novamente.',
      );
    }
    if (status == 404) {
      throw const AuthApiException('O recurso pedido não foi encontrado.');
    }
    if (status >= 500) {
      throw AuthApiException(
        'O servidor da API teve um erro ($status). Tenta novamente mais tarde.',
      );
    }
    String? detail;
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic> && decoded['detail'] is String) {
        detail = decoded['detail'] as String;
      }
    } on FormatException {
      // Corpo não é JSON — usa a mensagem genérica.
    }
    throw AuthApiException(detail ?? 'A API recusou o pedido ($status).');
  }

  static Uri _withTrailingSlash(Uri uri) {
    if (uri.path.endsWith('/')) {
      return uri;
    }
    return uri.replace(path: '${uri.path}/');
  }
}
