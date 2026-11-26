import 'package:material_ui/material_ui.dart';

import '../theme/app_colors.dart';

// =============================================================================
// Componentes partilhados pelos ecrãs do cliente (pedidos, detalhe,
// notificações e novo pedido). Ficam aqui para não repetir código.
// =============================================================================

/// Meses abreviados, como no protótipo Figma (formato pt-PT).
const _meses = [
  'jan.',
  'fev.',
  'mar.',
  'abr.',
  'mai.',
  'jun.',
  'jul.',
  'ago.',
  'set.',
  'out.',
  'nov.',
  'dez.',
];

/// Formata uma data como no Figma: "15 out. 2026" (ou "Por definir").
String formatarData(DateTime? data) {
  if (data == null) {
    return 'Por definir';
  }
  final local = data.toLocal();
  final dia = local.day.toString().padLeft(2, '0');
  return '$dia ${_meses[local.month - 1]} ${local.year}';
}

/// Formata uma data com hora: dd/mm/aaaa, hh:mm (como no Figma,
/// que usa toLocaleString("pt-PT") nas notificações).
String formatarDataHora(DateTime? data) {
  if (data == null) {
    return '—';
  }
  final local = data.toLocal();
  final dia = local.day.toString().padLeft(2, '0');
  final mes = local.month.toString().padLeft(2, '0');
  final hora = local.hour.toString().padLeft(2, '0');
  final minuto = local.minute.toString().padLeft(2, '0');
  return '$dia/$mes/${local.year}, $hora:$minuto';
}

/// Texto e cor do estado de um trabalho, na versão SIMPLIFICADA do cliente.
///
/// Tal como no protótipo Figma, o cliente não vê as etapas internas do
/// laboratório ("Por Iniciar", "Em Prova", "Em Espera"…):
///   - Concluído / Entregue (ou finalizado) → mostra esse estado, a verde;
///   - Cancelado / Rejeitado → mostra esse estado, a vermelho
///     (não existe no Figma, mas não se pode dizer que está em processamento);
///   - tudo o resto → "EM PROCESSAMENTO".
/// O texto da API é normalizado (sem acentos, minúsculas), porque não
/// sabemos se vem "em_processamento" ou "Em Processamento".
class EstadoInfo {
  const EstadoInfo(this.texto, this.cor);

  final String texto;
  final Color cor;

  /// true quando a produção já terminou (Concluído / Entregue).
  bool get terminado => cor == AppColors.greenOnline;

  factory EstadoInfo.de(String estado) {
    final normalizado = _semAcentos(estado.toLowerCase());
    final texto = estado.replaceAll('_', ' ').toUpperCase();

    if (normalizado.contains('conclu') ||
        normalizado.contains('finaliz') ||
        normalizado.contains('entreg')) {
      return EstadoInfo(texto, AppColors.greenOnline);
    }
    if (normalizado.contains('cancel') || normalizado.contains('rejeit')) {
      return EstadoInfo(texto, Colors.redAccent);
    }
    return const EstadoInfo('EM PROCESSAMENTO', AppColors.portalCyan);
  }

  static String _semAcentos(String texto) {
    const de = 'áàâãäéèêëíìîïóòôõöúùûüç';
    const para = 'aaaaaeeeeiiiiooooouuuuc';
    final buffer = StringBuffer();
    for (final rune in texto.runes) {
      final char = String.fromCharCode(rune);
      final indice = de.indexOf(char);
      buffer.write(indice >= 0 ? para[indice] : char);
    }
    return buffer.toString();
  }
}

/// Etiqueta colorida com o estado do trabalho.
class EtiquetaEstado extends StatelessWidget {
  const EtiquetaEstado({super.key, required this.estado});

  final String estado;

  @override
  Widget build(BuildContext context) {
    final info = EstadoInfo.de(estado);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: info.cor.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: info.cor.withValues(alpha: 0.4)),
      ),
      child: Text(
        info.texto,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(
          color: info.cor,
          fontSize: 10,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.4,
        ),
      ),
    );
  }
}

/// Cabeçalho dos ecrãs do cliente: faixa ESTGV, botão voltar e títulos.
class ClienteCabecalho extends StatelessWidget {
  const ClienteCabecalho({
    super.key,
    required this.secao,
    required this.titulo,
    this.subtitulo,
  });

  final String secao;
  final String titulo;
  final String? subtitulo;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Center(
            child: Text(
              'ESTGV • TECNOLOGIAS E DESIGN DE MULTIMÉDIA — PI4',
              style: TextStyle(
                color: AppColors.portalTextMuted,
                fontSize: 10,
                letterSpacing: 1.2,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              InkWell(
                onTap: () => Navigator.of(context).maybePop(),
                borderRadius: BorderRadius.circular(10),
                child: Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: AppColors.portalSurfaceDark,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.portalBorderLight),
                  ),
                  child: const Icon(
                    Icons.arrow_back_ios_new,
                    color: AppColors.portalTextSecondary,
                    size: 16,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  secao,
                  style: const TextStyle(
                    color: AppColors.portalGold,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.4,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            titulo,
            style: const TextStyle(
              color: AppColors.portalTextPrimary,
              fontSize: 26,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (subtitulo != null) ...[
            const SizedBox(height: 4),
            Text(
              subtitulo!,
              style: const TextStyle(
                color: AppColors.portalTextMuted,
                fontSize: 13,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// Mensagem de erro com botão "Tentar de novo".
class ClienteErro extends StatelessWidget {
  const ClienteErro({
    super.key,
    required this.mensagem,
    required this.onTentarDeNovo,
  });

  final String mensagem;
  final VoidCallback onTentarDeNovo;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.portalSurfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.redAccent.withValues(alpha: 0.4)),
      ),
      child: Column(
        children: [
          const Icon(Icons.error_outline, color: Colors.redAccent, size: 36),
          const SizedBox(height: 12),
          Text(
            mensagem,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.portalTextPrimary,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: onTentarDeNovo,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.portalGold,
              foregroundColor: AppColors.portalTextOnAccent,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            icon: const Icon(Icons.refresh, size: 18),
            label: const Text(
              'Tentar de novo',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

/// Mensagem para quando a lista está vazia.
class ClienteVazio extends StatelessWidget {
  const ClienteVazio({
    super.key,
    required this.icone,
    required this.titulo,
    required this.descricao,
  });

  final IconData icone;
  final String titulo;
  final String descricao;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.portalSurfaceDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.portalBorderLight),
      ),
      child: Column(
        children: [
          Icon(icone, color: AppColors.portalGold, size: 36),
          const SizedBox(height: 12),
          Text(
            titulo,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.portalTextPrimary,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            descricao,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.portalTextMuted,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}
