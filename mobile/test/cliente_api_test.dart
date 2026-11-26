import 'dart:convert';

import 'package:ficha7_app/pages/services/auth_api.dart';
import 'package:ficha7_app/pages/services/cliente_api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  setUp(() {
    AuthApi.currentSession = const AuthSession(
      accessToken: 'client-token',
      refreshToken: 'refresh-token',
      user: AuthenticatedUser(
        id: 12,
        email: 'cliente@example.com',
        profile: 'cliente',
        permissions: [],
      ),
    );
  });

  tearDown(() {
    AuthApi.currentSession = null;
  });

  test(
    'uses the authenticated API for client orders and notifications',
    () async {
      final requests = <String>[];
      final client = MockClient((request) async {
        requests.add('${request.method} ${request.url.path}');
        expect(request.headers['Authorization'], 'Bearer client-token');

        switch (request.url.path) {
          case '/api/v1/trabalhos/':
            return http.Response(
              jsonEncode([
                {
                  'id': 7,
                  'paciente_nome': 'Ana Silva',
                  'tipo_trabalho_nome': 'Coroa',
                  'estado': 'Em Prova',
                },
              ]),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          case '/api/v1/trabalhos/7/':
            return http.Response(
              jsonEncode({
                'id': 7,
                'paciente_nome': 'Ana Silva',
                'tipo_trabalho_nome': 'Coroa',
                'estado': 'Em Prova',
              }),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          case '/api/v1/notificacoes/':
            return http.Response(
              jsonEncode([
                {
                  'id': 9,
                  'titulo': 'Atualização',
                  'conteudo': 'O trabalho avançou.',
                  'trabalho': 7,
                  'criada_em': '2026-11-26T10:00:00Z',
                },
              ]),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          case '/api/v1/notificacoes/9/ler/':
            return http.Response(
              '{}',
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          default:
            fail('Pedido inesperado: ${request.method} ${request.url}');
        }
      });
      addTearDown(client.close);
      final api = ClienteApi(
        client: client,
        baseUri: Uri.parse('https://api.example.test/api/v1/'),
      );

      final trabalhos = await api.listarTrabalhos();
      final trabalho = await api.obterTrabalho(7);
      final notificacoes = await api.listarNotificacoes();
      await api.marcarNotificacaoLida(9);

      expect(trabalhos.single.pacienteNome, 'Ana Silva');
      expect(trabalho.id, 7);
      expect(notificacoes.single.trabalhoId, 7);
      expect(requests, [
        'GET /api/v1/trabalhos/',
        'GET /api/v1/trabalhos/7/',
        'GET /api/v1/notificacoes/',
        'POST /api/v1/notificacoes/9/ler/',
      ]);
    },
  );
}
