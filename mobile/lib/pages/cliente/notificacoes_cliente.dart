import 'package:material_ui/material_ui.dart';

import '../route_names.dart';
import '../services/auth_api.dart';
import '../services/cliente_api.dart';
import '../theme/app_colors.dart';
import 'cliente_widgets.dart';

/// Ecrã "Notificações" do cliente.
///
/// - Lista as notificações (GET notificacoes/).
/// - Tocar numa notificação por ler marca-a como lida
///   (POST notificacoes/{id}/ler/).
/// - "Marcar todas como lidas" faz o mesmo para todas as que faltam.
/// - Se a notificação estiver associada a um trabalho, mostra "Abrir trabalho".
class NotificacoesClientePage extends StatefulWidget {
  const NotificacoesClientePage({super.key, this.clienteApi});

  final ClienteApi? clienteApi;

  @override
  State<NotificacoesClientePage> createState() =>
      _NotificacoesClientePageState();
}

class _NotificacoesClientePageState extends State<NotificacoesClientePage> {
  late final ClienteApi _api = widget.clienteApi ?? ClienteApi.instance;

  bool _aCarregar = true;
  String? _erro;
  List<Notificacao> _notificacoes = const [];

  /// IDs das notificações que estão a ser marcadas neste momento
  /// (para mostrar um indicador e evitar pedidos repetidos).
  final Set<int> _aMarcar = {};
  bool _aMarcarTodas = false;

  int get _porLer => _notificacoes.where((n) => !n.lida).length;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    setState(() {
      _aCarregar = true;
      _erro = null;
    });
    try {
      final notificacoes = await _api.listarNotificacoes();
      // Mais recentes primeiro.
      notificacoes.sort((a, b) {
        final da = a.criadaEm ?? DateTime(0);
        final db = b.criadaEm ?? DateTime(0);
        return db.compareTo(da);
      });
      if (!mounted) return;
      setState(() => _notificacoes = notificacoes);
    } on AuthApiException catch (e) {
      if (!mounted) return;
      setState(() => _erro = e.message);
    } finally {
      if (mounted) {
        setState(() => _aCarregar = false);
      }
    }
  }

  /// Substitui na lista a notificação com este id pela versão "lida".
  void _atualizarComoLida(int id) {
    setState(() {
      _notificacoes = [
        for (final n in _notificacoes) n.id == id ? n.marcadaComoLida() : n,
      ];
    });
  }

  Future<void> _marcarComoLida(Notificacao notificacao) async {
    if (notificacao.lida || _aMarcar.contains(notificacao.id)) {
      return;
    }
    setState(() => _aMarcar.add(notificacao.id));
    try {
      await _api.marcarNotificacaoLida(notificacao.id);
      if (!mounted) return;
      _atualizarComoLida(notificacao.id);
    } on AuthApiException catch (e) {
      _mostrarMensagem(e.message);
    } finally {
      if (mounted) {
        setState(() => _aMarcar.remove(notificacao.id));
      }
    }
  }

  Future<void> _marcarTodas() async {
    final porLer = _notificacoes.where((n) => !n.lida).toList();
    if (porLer.isEmpty || _aMarcarTodas) {
      return;
    }
    setState(() => _aMarcarTodas = true);
    var falhas = 0;
    // Não existe endpoint "marcar todas", por isso marcamos uma a uma.
    for (final notificacao in porLer) {
      try {
        await _api.marcarNotificacaoLida(notificacao.id);
        if (!mounted) return;
        _atualizarComoLida(notificacao.id);
      } on AuthApiException {
        falhas++;
      }
    }
    if (!mounted) return;
    setState(() => _aMarcarTodas = false);
    if (falhas > 0) {
      _mostrarMensagem(
        'Não foi possível marcar $falhas '
        '${falhas == 1 ? 'notificação' : 'notificações'} como lida.',
      );
    }
  }

  void _abrirPedido(Notificacao notificacao) {
    final trabalhoId = notificacao.trabalhoId;
    if (trabalhoId == null) return;
    _marcarComoLida(notificacao);
    Navigator.of(
      context,
    ).pushNamed(AppRouteNames.clientPedidoDetalhePath, arguments: trabalhoId);
  }

  void _mostrarMensagem(String texto) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(texto),
        backgroundColor: AppColors.portalSurfaceDark,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.portalBgDark,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const ClienteCabecalho(
              secao: 'NOTIFICAÇÕES',
              titulo: 'Caixa de entrada',
              subtitulo: 'Notas e alterações dos seus trabalhos.',
            ),
            Expanded(child: _buildConteudo()),
          ],
        ),
      ),
    );
  }

  Widget _buildConteudo() {
    if (_aCarregar && _notificacoes.isEmpty && _erro == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.portalGold),
      );
    }

    return RefreshIndicator(
      color: AppColors.portalGold,
      backgroundColor: AppColors.portalSurfaceDark,
      onRefresh: _carregar,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          if (_erro != null)
            ClienteErro(mensagem: _erro!, onTentarDeNovo: _carregar)
          else if (_notificacoes.isEmpty)
            const ClienteVazio(
              icone: Icons.notifications_none,
              titulo: 'Sem notificações',
              descricao:
                  'Quando o laboratório atualizar um pedido, '
                  'será avisado aqui.',
            )
          else ...[
            _buildResumo(),
            const SizedBox(height: 14),
            for (final notificacao in _notificacoes) ...[
              _NotificacaoCard(
                notificacao: notificacao,
                aMarcar: _aMarcar.contains(notificacao.id),
                onTap: () => _marcarComoLida(notificacao),
                onVerPedido: notificacao.trabalhoId == null
                    ? null
                    : () => _abrirPedido(notificacao),
              ),
              const SizedBox(height: 12),
            ],
          ],
        ],
      ),
    );
  }

  /// Contador "X por ler" + botão "Marcar todas como lidas".
  Widget _buildResumo() {
    return Row(
      children: [
        Expanded(
          child: Text(
            '$_porLer por ler · ${_notificacoes.length} '
            '${_notificacoes.length == 1 ? 'notificação' : 'notificações'}',
            style: const TextStyle(
              color: AppColors.portalTextMuted,
              fontSize: 12,
            ),
          ),
        ),
        TextButton.icon(
          onPressed: _porLer == 0 || _aMarcarTodas ? null : _marcarTodas,
          icon: _aMarcarTodas
              ? const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: AppColors.portalGold,
                  ),
                )
              : const Icon(Icons.done_all, size: 18),
          label: const Text('Marcar todas como lidas'),
          style: TextButton.styleFrom(
            foregroundColor: AppColors.portalGold,
            disabledForegroundColor: AppColors.portalTextMuted,
            textStyle: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }
}

class _NotificacaoCard extends StatelessWidget {
  const _NotificacaoCard({
    required this.notificacao,
    required this.aMarcar,
    required this.onTap,
    required this.onVerPedido,
  });

  final Notificacao notificacao;
  final bool aMarcar;
  final VoidCallback onTap;
  final VoidCallback? onVerPedido;

  /// Ícone conforme o tipo de notificação (procura palavras-chave).
  IconData get _icone {
    final tipo = (notificacao.tipo ?? '').toLowerCase();
    if (tipo.contains('estado')) return Icons.sync_alt;
    if (tipo.contains('foto') || tipo.contains('imagem')) {
      return Icons.camera_alt_outlined;
    }
    if (tipo.contains('mensagem') || tipo.contains('nota')) {
      return Icons.chat_bubble_outline;
    }
    if (tipo.contains('consulta')) return Icons.event_outlined;
    return Icons.notifications_outlined;
  }

  @override
  Widget build(BuildContext context) {
    final naoLida = !notificacao.lida;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.portalSurfaceDark,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: naoLida
                ? AppColors.portalCyan.withValues(alpha: 0.35)
                : AppColors.portalBorderLight,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: AppColors.portalUpdateBackground,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(_icone, color: AppColors.portalCyan, size: 22),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        notificacao.titulo,
                        style: TextStyle(
                          color: AppColors.portalTextPrimary,
                          fontWeight: naoLida
                              ? FontWeight.bold
                              : FontWeight.w500,
                          fontSize: 14,
                        ),
                      ),
                      if (notificacao.conteudo.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          notificacao.conteudo,
                          style: const TextStyle(
                            color: AppColors.portalDescriptionText,
                            fontSize: 13,
                          ),
                        ),
                      ],
                      const SizedBox(height: 6),
                      Text(
                        formatarDataHora(notificacao.criadaEm),
                        style: const TextStyle(
                          color: AppColors.portalTimestampText,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                // Indicador: a marcar (spinner) / por ler (ponto) / lida (nada)
                if (aMarcar)
                  const SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: AppColors.portalCyan,
                    ),
                  )
                else if (naoLida)
                  Container(
                    margin: const EdgeInsets.only(top: 4),
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: AppColors.portalCyan,
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
            if (onVerPedido != null) ...[
              const SizedBox(height: 12),
              const Divider(color: AppColors.portalBorderLight, height: 1),
              const SizedBox(height: 8),
              InkWell(
                onTap: onVerPedido,
                borderRadius: BorderRadius.circular(6),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Abrir trabalho #${notificacao.trabalhoId}',
                        style: const TextStyle(
                          color: AppColors.portalGold,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(width: 4),
                      const Icon(
                        Icons.chevron_right,
                        color: AppColors.portalGold,
                        size: 16,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
