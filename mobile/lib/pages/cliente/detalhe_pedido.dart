import 'package:material_ui/material_ui.dart';

import '../services/auth_api.dart';
import '../services/cliente_api.dart';
import '../theme/app_colors.dart';
import 'cliente_widgets.dart';

/// Ecrã "Detalhe do pedido": mostra um trabalho do cliente.
///
/// Recebe apenas o [trabalhoId] e pede os dados atualizados à API
/// (GET trabalhos/{id}/), em vez de reaproveitar os da lista — assim
/// o detalhe está sempre atualizado, mesmo quando aberto a partir de
/// uma notificação.
///
/// A data_limite (interna do laboratório) nunca é mostrada.
class DetalhePedidoPage extends StatefulWidget {
  const DetalhePedidoPage({
    super.key,
    required this.trabalhoId,
    this.clienteApi,
  });

  final int trabalhoId;
  final ClienteApi? clienteApi;

  @override
  State<DetalhePedidoPage> createState() => _DetalhePedidoPageState();
}

class _DetalhePedidoPageState extends State<DetalhePedidoPage> {
  late final ClienteApi _api = widget.clienteApi ?? ClienteApi.instance;

  bool _aCarregar = true;
  String? _erro;
  Trabalho? _trabalho;

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
      final trabalho = await _api.obterTrabalho(widget.trabalhoId);
      if (!mounted) return;
      setState(() => _trabalho = trabalho);
    } on AuthApiException catch (e) {
      if (!mounted) return;
      setState(() => _erro = e.message);
    } finally {
      if (mounted) {
        setState(() => _aCarregar = false);
      }
    }
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
              secao: 'FICHA DO TRABALHO',
              titulo: 'Ficha do trabalho',
            ),
            Expanded(child: _buildConteudo()),
          ],
        ),
      ),
    );
  }

  Widget _buildConteudo() {
    final trabalho = _trabalho;

    if (_aCarregar && trabalho == null) {
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
          else if (trabalho != null) ...[
            _buildCabecalhoTrabalho(trabalho),
            const SizedBox(height: 16),
            _buildEstadoProducao(trabalho),
            const SizedBox(height: 16),
            _buildResumo(trabalho),
          ],
        ],
      ),
    );
  }

  /// Topo da ficha (como no Figma): referência, tipo de trabalho,
  /// paciente e etiqueta de estado.
  Widget _buildCabecalhoTrabalho(Trabalho trabalho) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.portalCardDark,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.portalBorderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '#${trabalho.id}',
            style: const TextStyle(
              color: AppColors.portalGold,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.1,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            trabalho.tipoTrabalhoNome,
            style: const TextStyle(
              color: AppColors.portalTextPrimary,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            trabalho.pacienteNome,
            style: const TextStyle(
              color: AppColors.portalTextMuted,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 14),
          EtiquetaEstado(estado: trabalho.estado),
        ],
      ),
    );
  }

  /// "ESTADO DA PRODUÇÃO" — no Figma é isto que o cliente vê em vez da
  /// data limite (que é interna do laboratório).
  Widget _buildEstadoProducao(Trabalho trabalho) {
    final estado = EstadoInfo.de(trabalho.estado);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.portalSurfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.portalBorderLight),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: estado.cor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(Icons.inventory_2_outlined, color: estado.cor),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'ESTADO DA PRODUÇÃO',
                  style: TextStyle(
                    color: AppColors.portalTextMuted,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  estado.texto,
                  style: const TextStyle(
                    color: AppColors.portalTextPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  estado.terminado ? 'Produção terminada' : 'Produção em curso',
                  style: const TextStyle(
                    color: AppColors.portalTextMuted,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// "Resumo do trabalho" com os dados que a API devolve ao cliente.
  Widget _buildResumo(Trabalho trabalho) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 6),
      decoration: BoxDecoration(
        color: AppColors.portalSurfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.portalBorderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Resumo do trabalho',
            style: TextStyle(
              color: AppColors.portalTextPrimary,
              fontSize: 15,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 2),
          const Text(
            'Informação clínica disponibilizada ao cliente',
            style: TextStyle(color: AppColors.portalTextMuted, fontSize: 12),
          ),
          const SizedBox(height: 6),
          _InfoLinha(
            rotulo: 'PRÓXIMA CONSULTA',
            valor: formatarData(trabalho.dataProximaConsulta),
          ),
          const Divider(color: AppColors.portalBorderLight, height: 1),
          _InfoLinha(rotulo: 'PACIENTE', valor: trabalho.pacienteNome),
          const Divider(color: AppColors.portalBorderLight, height: 1),
          _InfoLinha(
            rotulo: 'NATUREZA DO TRABALHO',
            valor: trabalho.natureza ?? '—',
          ),
          const Divider(color: AppColors.portalBorderLight, height: 1),
          _InfoLinha(
            rotulo: 'TIPO DE TRABALHO',
            valor: trabalho.tipoTrabalhoNome,
          ),
          const Divider(color: AppColors.portalBorderLight, height: 1),
          _InfoLinha(rotulo: 'REFERÊNCIA', valor: '#${trabalho.id}'),
          const Divider(color: AppColors.portalBorderLight, height: 1),
          _InfoLinha(rotulo: 'ENCOMENDA', valor: trabalho.encomenda ?? '—'),
          if (trabalho.dataFinalizacao != null) ...[
            const Divider(color: AppColors.portalBorderLight, height: 1),
            _InfoLinha(
              rotulo: 'DATA DE FINALIZAÇÃO',
              valor: formatarData(trabalho.dataFinalizacao),
            ),
          ],
        ],
      ),
    );
  }
}

class _InfoLinha extends StatelessWidget {
  const _InfoLinha({required this.rotulo, required this.valor});

  final String rotulo;
  final String valor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        children: [
          Text(
            rotulo,
            style: const TextStyle(
              color: AppColors.portalTextMuted,
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              valor,
              textAlign: TextAlign.right,
              style: const TextStyle(
                color: AppColors.portalTextPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
