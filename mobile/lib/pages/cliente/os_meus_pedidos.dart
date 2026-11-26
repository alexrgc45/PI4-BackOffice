import 'package:material_ui/material_ui.dart';

import '../route_names.dart';
import '../services/auth_api.dart';
import '../services/cliente_api.dart';
import '../theme/app_colors.dart';
import 'cliente_widgets.dart';

/// Ecrã "Os meus Pedidos": lista dos trabalhos do cliente autenticado.
///
/// Tem 4 estados possíveis: a carregar, erro, lista vazia e lista com dados.
/// Puxar a lista para baixo volta a pedir os dados à API.
class OsMeusPedidosPage extends StatefulWidget {
  const OsMeusPedidosPage({super.key, this.clienteApi});

  /// Permite injetar outra instância (útil em testes).
  final ClienteApi? clienteApi;

  @override
  State<OsMeusPedidosPage> createState() => _OsMeusPedidosPageState();
}

class _OsMeusPedidosPageState extends State<OsMeusPedidosPage> {
  late final ClienteApi _api = widget.clienteApi ?? ClienteApi.instance;

  bool _aCarregar = true;
  String? _erro;
  List<Trabalho> _trabalhos = const [];

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
      final trabalhos = await _api.listarTrabalhos();
      if (!mounted) return;
      setState(() => _trabalhos = trabalhos);
    } on AuthApiException catch (e) {
      if (!mounted) return;
      setState(() => _erro = e.message);
    } finally {
      if (mounted) {
        setState(() => _aCarregar = false);
      }
    }
  }

  void _abrirDetalhe(Trabalho trabalho) {
    Navigator.of(
      context,
    ).pushNamed(AppRouteNames.clientPedidoDetalhePath, arguments: trabalho.id);
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
              secao: 'PORTAL DA CLÍNICA',
              titulo: 'Os meus Pedidos',
              subtitulo: 'Apenas os pedidos associados à entidade autenticada.',
            ),
            Expanded(child: _buildConteudo()),
          ],
        ),
      ),
    );
  }

  Widget _buildConteudo() {
    // 1) A carregar (só na primeira vez; no "puxar para atualizar" a lista
    //    antiga fica visível e aparece o indicador do RefreshIndicator).
    if (_aCarregar && _trabalhos.isEmpty && _erro == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.portalGold),
      );
    }

    // O RefreshIndicator precisa sempre de uma lista que faça scroll,
    // por isso até os estados de erro e vazio estão dentro de um ListView.
    return RefreshIndicator(
      color: AppColors.portalGold,
      backgroundColor: AppColors.portalSurfaceDark,
      onRefresh: _carregar,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          // 2) Erro
          if (_erro != null)
            ClienteErro(mensagem: _erro!, onTentarDeNovo: _carregar)
          // 3) Lista vazia
          else if (_trabalhos.isEmpty)
            const ClienteVazio(
              icone: Icons.receipt_long_outlined,
              titulo: 'Ainda não tem pedidos',
              descricao:
                  'Quando enviar um pedido ao laboratório, '
                  'ele aparece aqui.',
            )
          // 4) Lista com dados
          else ...[
            // Título da lista, como no Figma ("Pedidos da entidade").
            const Text(
              'Pedidos da entidade',
              style: TextStyle(
                color: AppColors.portalTextPrimary,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Histórico e produção em curso · ${_trabalhos.length} '
              '${_trabalhos.length == 1 ? 'pedido' : 'pedidos'}',
              style: const TextStyle(
                color: AppColors.portalTextMuted,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 12),
            for (final trabalho in _trabalhos) ...[
              _PedidoCard(
                trabalho: trabalho,
                onTap: () => _abrirDetalhe(trabalho),
              ),
              const SizedBox(height: 12),
            ],
          ],
        ],
      ),
    );
  }
}

/// Cartão de um pedido na lista (mesmo visual da página principal).
class _PedidoCard extends StatelessWidget {
  const _PedidoCard({required this.trabalho, required this.onTap});

  final Trabalho trabalho;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final natureza = trabalho.natureza;
    final digital =
        natureza != null && natureza.toLowerCase().contains('digit');

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.portalSurfaceDark,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.portalBorderLight),
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: AppColors.portalRoleBackground,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                digital
                    ? Icons.description_outlined
                    : Icons.view_in_ar_outlined,
                color: AppColors.portalCyan,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    natureza == null || natureza.isEmpty
                        ? '#${trabalho.id}'
                        : '#${trabalho.id} · $natureza',
                    style: const TextStyle(
                      color: AppColors.portalTextMuted,
                      fontSize: 11,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    trabalho.pacienteNome,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.portalTextPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    trabalho.tipoTrabalhoNome,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.portalTextMuted,
                      fontSize: 13,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(
                        Icons.event_outlined,
                        size: 14,
                        color: AppColors.portalGold,
                      ),
                      const SizedBox(width: 4),
                      Flexible(
                        child: Text(
                          'Próxima consulta: '
                          '${formatarData(trabalho.dataProximaConsulta)}',
                          style: const TextStyle(
                            color: AppColors.portalDescriptionText,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  EtiquetaEstado(estado: trabalho.estado),
                ],
              ),
            ),
            const SizedBox(width: 6),
            const Icon(Icons.chevron_right, color: AppColors.portalTextMuted),
          ],
        ),
      ),
    );
  }
}
