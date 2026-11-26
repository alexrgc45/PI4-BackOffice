import 'package:material_ui/material_ui.dart';

import '../theme/app_colors.dart';
import 'cliente_widgets.dart';

/// Ecrã "Novo Pedido" do cliente — SÓ INTERFACE.
///
/// O endpoint para criar pedidos ainda não existe na API, por isso o
/// botão "Submeter pedido" valida o formulário e mostra um resumo,
/// mas não guarda nada.
///
/// Segue o protótipo Figma ("Novo pedido · Dados clínicos"):
///   Paciente:  nome *, sexo *, idade *
///   Clínico:   médico responsável *
///   Trabalho:  tipo *, fluxo (Físico / Digital, por defeito Digital),
///              materiais necessários * (vários, escritos pelo cliente)
///   Dentes:    odontograma FDI (11–48) — OPCIONAL, só quando relevante
///   Datas:     próxima consulta (opcional)
///   Notas:     notas para o laboratório (cor, indicações clínicas…)
///   Anexos:    fotografias / ficheiro STL (ainda sem envio para a API)
///
/// Numeração FDI:
///   - 1.º dígito = quadrante: 1 superior direito, 2 superior esquerdo,
///                             3 inferior esquerdo, 4 inferior direito
///   - 2.º dígito = dente, de 1 (incisivo central) a 8 (siso)
/// O odontograma é desenhado como se estivéssemos de frente para o paciente:
/// a direita do paciente aparece à esquerda do ecrã.
class NovoPedidoPage extends StatefulWidget {
  const NovoPedidoPage({super.key});

  @override
  State<NovoPedidoPage> createState() => _NovoPedidoPageState();
}

class _NovoPedidoPageState extends State<NovoPedidoPage> {
  final _formKey = GlobalKey<FormState>();

  final _pacienteController = TextEditingController();
  final _idadeController = TextEditingController();
  final _medicoController = TextEditingController();
  final _materialController = TextEditingController();
  final _notasController = TextEditingController();

  // Lista provisória. Quando existir um endpoint na API para os tipos de
  // trabalho, deve passar a vir de lá.
  static const _tiposTrabalho = [
    'Coroa',
    'Ponte',
    'Prótese acrílica',
    'Prótese esquelética',
    'Facetas cerâmicas',
    'Goteira',
    'Outro',
  ];
  // Opções iguais às do Figma.
  static const _sexos = ['Feminino', 'Masculino', 'Outro / não indicado'];
  static const _fluxos = ['Físico', 'Digital'];

  String? _sexo;
  String? _tipoTrabalho;
  // Como no Figma, o fluxo começa em "Digital" (há sempre um escolhido).
  String _fluxo = 'Digital';
  DateTime? _proximaConsulta;

  /// Materiais necessários. Como no Figma, começa com "Dissilicato de lítio"
  /// e o cliente pode acrescentar ou remover materiais.
  final List<String> _materiais = ['Dissilicato de lítio'];

  // Uma chave por campo validado. Servem para, depois do validate(),
  // descobrir qual é o PRIMEIRO campo com erro e fazer scroll até ele.
  final _kNome = GlobalKey<FormFieldState<String>>();
  final _kSexo = GlobalKey<FormFieldState<String>>();
  final _kIdade = GlobalKey<FormFieldState<String>>();
  final _kMedico = GlobalKey<FormFieldState<String>>();
  final _kTipo = GlobalKey<FormFieldState<String>>();
  final _kMateriais = GlobalKey<FormFieldState<List<String>>>();

  /// Os campos pela ordem em que aparecem no ecrã (de cima para baixo).
  List<GlobalKey<FormFieldState<Object?>>> get _camposPorOrdem => [
    _kNome,
    _kSexo,
    _kIdade,
    _kMedico,
    _kTipo,
    _kMateriais,
  ];

  /// Dentes selecionados no odontograma (números FDI).
  /// Um Set não permite repetidos: cada dente só pode estar uma vez.
  final Set<int> _dentes = {};

  // Arcada superior: 18 → 11 | 21 → 28
  static const List<int> _superiorDireito = [18, 17, 16, 15, 14, 13, 12, 11];
  static const List<int> _superiorEsquerdo = [21, 22, 23, 24, 25, 26, 27, 28];
  // Arcada inferior: 48 → 41 | 31 → 38
  static const List<int> _inferiorDireito = [48, 47, 46, 45, 44, 43, 42, 41];
  static const List<int> _inferiorEsquerdo = [31, 32, 33, 34, 35, 36, 37, 38];

  /// Abaixo desta largura de ecrã cada arcada é partida em duas linhas.
  static const double _larguraEcraEstreito = 600;

  /// Tamanho mínimo de cada dente (área de toque confortável com o dedo).
  static const double _tamanhoMinimoDente = 32;

  @override
  void dispose() {
    _pacienteController.dispose();
    _idadeController.dispose();
    _medicoController.dispose();
    _materialController.dispose();
    _notasController.dispose();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Ações
  // ---------------------------------------------------------------------------

  void _alternarDente(int dente) {
    setState(() {
      // remove() devolve false se o dente não estava selecionado → adiciona.
      if (!_dentes.remove(dente)) {
        _dentes.add(dente);
      }
    });
  }

  void _selecionarArcada(List<int> dentes) {
    setState(() {
      if (dentes.every(_dentes.contains)) {
        _dentes.removeAll(dentes);
      } else {
        _dentes.addAll(dentes);
      }
    });
  }

  void _limparDentes() {
    setState(_dentes.clear);
  }

  /// Acrescenta o material escrito na caixa (sem repetidos), como o
  /// botão "Adicionar" do Figma.
  void _adicionarMaterial() {
    final material = _materialController.text.trim();
    if (material.isEmpty || _materiais.contains(material)) {
      return;
    }
    setState(() => _materiais.add(material));
    _materialController.clear();
    _revalidarMateriais();
  }

  void _removerMaterial(String material) {
    setState(() => _materiais.remove(material));
    _revalidarMateriais();
  }

  /// Se o campo dos materiais já está a mostrar erro, volta a validar,
  /// para o erro desaparecer logo que se acrescenta um material.
  void _revalidarMateriais() {
    final campo = _kMateriais.currentState;
    if (campo != null && campo.hasError) {
      campo.validate();
    }
  }

  /// Os anexos ainda não podem ser enviados: a API não tem endpoint.
  void _anexoIndisponivel() {
    _mostrarMensagem(
      'O envio de fotografias e ficheiros STL ainda não está disponível.',
    );
  }

  /// Abre o calendário (tema escuro/dourado) e devolve a data escolhida.
  Future<DateTime?> _escolherData({
    required DateTime? atual,
    required String titulo,
  }) {
    final hoje = DateTime.now();
    final primeiro = DateTime(hoje.year, hoje.month, hoje.day);
    return showDatePicker(
      context: context,
      initialDate: atual ?? primeiro,
      firstDate: primeiro,
      lastDate: DateTime(hoje.year + 2),
      helpText: titulo,
      cancelText: 'Cancelar',
      confirmText: 'OK',
      builder: (context, child) => Theme(
        data: ThemeData.dark().copyWith(
          colorScheme: const ColorScheme.dark(
            primary: AppColors.portalGold,
            onPrimary: AppColors.portalTextOnAccent,
            surface: AppColors.portalSurfaceDark,
          ),
        ),
        child: child!,
      ),
    );
  }

  void _submeter() {
    // validate() corre o validator de TODOS os campos do Form
    // e mostra as mensagens de erro por baixo de cada um.
    final formularioValido = _formKey.currentState?.validate() ?? false;
    if (!formularioValido) {
      _irParaPrimeiroErro();
      _mostrarMensagem('Preencha o paciente, sexo, idade e materiais.');
      return;
    }

    final dentesOrdenados = _dentes.toList()..sort();
    final idade = _idadeController.text.trim();
    final notas = _notasController.text.trim();
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.portalSurfaceDark,
        title: const Text(
          'Resumo do pedido',
          style: TextStyle(color: AppColors.portalTextPrimary),
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _linhaResumo('Paciente', _pacienteController.text.trim()),
              _linhaResumo('Sexo', _sexo ?? '—'),
              // Só acrescenta "anos" quando há idade.
              _linhaResumo('Idade', idade.isEmpty ? '—' : '$idade anos'),
              _linhaResumo('Médico', _medicoController.text.trim()),
              _linhaResumo('Tipo', _tipoTrabalho ?? '—'),
              _linhaResumo('Fluxo', _fluxo),
              _linhaResumo('Materiais', _materiais.join(', ')),
              _linhaResumo(
                'Dentes',
                dentesOrdenados.isEmpty ? '—' : dentesOrdenados.join(', '),
              ),
              _linhaResumo('Próxima consulta', formatarData(_proximaConsulta)),
              _linhaResumo('Notas', notas.isEmpty ? '—' : notas),
              const SizedBox(height: 12),
              const Text(
                'O envio ainda não está disponível: a API do laboratório '
                'ainda não tem o endpoint para criar pedidos. '
                'Nada foi guardado.',
                style: TextStyle(color: AppColors.portalGold, fontSize: 12),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text(
              'Fechar',
              style: TextStyle(color: AppColors.portalGold),
            ),
          ),
        ],
      ),
    );
  }

  /// Percorre os campos de cima para baixo e faz scroll até ao primeiro
  /// que ficou com erro.
  void _irParaPrimeiroErro() {
    for (final chave in _camposPorOrdem) {
      final campo = chave.currentState;
      final contexto = chave.currentContext;
      if (campo != null && campo.hasError && contexto != null) {
        Scrollable.ensureVisible(
          contexto,
          duration: const Duration(milliseconds: 350),
          curve: Curves.easeInOut,
          alignment: 0.15, // deixa o campo um pouco abaixo do topo
        );
        return;
      }
    }
  }

  void _mostrarMensagem(String texto) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(texto),
        backgroundColor: AppColors.portalSurfaceDark,
      ),
    );
  }

  Widget _linhaResumo(String rotulo, String valor) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text.rich(
        TextSpan(
          children: [
            TextSpan(
              text: '$rotulo: ',
              style: const TextStyle(color: AppColors.portalTextMuted),
            ),
            TextSpan(
              text: valor,
              style: const TextStyle(color: AppColors.portalTextPrimary),
            ),
          ],
        ),
        style: const TextStyle(fontSize: 13),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Validações
  // ---------------------------------------------------------------------------

  static String? _obrigatorio(String? valor, String mensagem) {
    return (valor == null || valor.trim().isEmpty) ? mensagem : null;
  }

  static String? _validarIdade(String? valor) {
    final texto = valor?.trim() ?? '';
    if (texto.isEmpty) {
      return 'Indique a idade do paciente.';
    }
    final idade = int.tryParse(texto);
    if (idade == null || idade < 0 || idade > 120) {
      return 'Idade inválida (0 a 120).';
    }
    return null;
  }

  // ---------------------------------------------------------------------------
  // Ecrã
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.portalBgDark,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const ClienteCabecalho(
              secao: 'NOVO PEDIDO',
              titulo: 'Dados clínicos',
              subtitulo: 'Informação para avaliação pelo laboratório.',
            ),
            Expanded(
              child: Form(
                key: _formKey,
                // IMPORTANTE: SingleChildScrollView + Column, e NÃO ListView.
                // O ListView só constrói os widgets visíveis no ecrã; os campos
                // que saem do ecrã são destruídos e deixam de pertencer ao Form,
                // por isso o validate() ignorava-os. Assim, todos os campos
                // existem sempre e são todos validados.
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _buildAvisoSemEnvio(),

                      // ---------------- Paciente ----------------
                      _tituloSecao('PACIENTE'),
                      _rotulo('Nome do paciente *'),
                      TextFormField(
                        key: _kNome,
                        controller: _pacienteController,
                        textCapitalization: TextCapitalization.words,
                        style: _estiloTexto,
                        decoration: _decoracao(
                          'Nome completo',
                          Icons.person_outline,
                        ),
                        validator: (v) =>
                            _obrigatorio(v, 'Indique o nome do paciente.'),
                      ),
                      const SizedBox(height: 16),
                      _rotulo('Sexo *'),
                      DropdownButtonFormField<String>(
                        key: _kSexo,
                        initialValue: _sexo,
                        isExpanded: true,
                        dropdownColor: AppColors.portalSurfaceDark,
                        style: _estiloTexto,
                        decoration: _decoracao('Selecionar', Icons.wc_outlined),
                        items: [
                          for (final sexo in _sexos)
                            DropdownMenuItem(value: sexo, child: Text(sexo)),
                        ],
                        onChanged: (v) => setState(() => _sexo = v),
                        validator: (v) =>
                            v == null ? 'Selecione o sexo.' : null,
                      ),
                      const SizedBox(height: 16),
                      _rotulo('Idade *'),
                      TextFormField(
                        key: _kIdade,
                        controller: _idadeController,
                        keyboardType: TextInputType.number,
                        style: _estiloTexto,
                        decoration: _decoracao('Ex.: 45', Icons.cake_outlined),
                        validator: _validarIdade,
                      ),

                      // ---------------- Clínico ----------------
                      _tituloSecao('CLÍNICO'),
                      _rotulo('Médico responsável *'),
                      TextFormField(
                        key: _kMedico,
                        controller: _medicoController,
                        textCapitalization: TextCapitalization.words,
                        style: _estiloTexto,
                        decoration: _decoracao(
                          'Ex.: Dra. Inês Matos',
                          Icons.medical_services_outlined,
                        ),
                        validator: (v) =>
                            _obrigatorio(v, 'Selecione o médico responsável.'),
                      ),

                      // ---------------- Trabalho ----------------
                      _tituloSecao('TRABALHO E MATERIAIS'),
                      _rotulo('Tipo de trabalho *'),
                      DropdownButtonFormField<String>(
                        key: _kTipo,
                        initialValue: _tipoTrabalho,
                        // Ocupa a largura toda e corta textos longos com "…"
                        // em vez de transbordar em ecrãs estreitos.
                        isExpanded: true,
                        dropdownColor: AppColors.portalSurfaceDark,
                        style: _estiloTexto,
                        decoration: _decoracao(
                          'Selecione o tipo',
                          Icons.category_outlined,
                        ),
                        items: [
                          for (final tipo in _tiposTrabalho)
                            DropdownMenuItem(value: tipo, child: Text(tipo)),
                        ],
                        onChanged: (v) => setState(() => _tipoTrabalho = v),
                        validator: (v) =>
                            v == null ? 'Selecione o tipo de trabalho.' : null,
                      ),
                      const SizedBox(height: 16),
                      _rotulo('Fluxo'),
                      _CampoOpcoes(
                        opcoes: _fluxos,
                        valor: _fluxo,
                        icones: const [
                          Icons.view_in_ar_outlined,
                          Icons.description_outlined,
                        ],
                        onChanged: (v) => setState(() => _fluxo = v),
                      ),
                      const SizedBox(height: 16),
                      _rotulo('Materiais necessários *'),
                      _buildMateriais(),

                      // ---------------- Dentes (opcional) ----------------
                      const SizedBox(height: 22),
                      _buildOdontograma(),

                      // ---------------- Consulta ----------------
                      _tituloSecao('CONSULTA'),
                      _rotulo('Próxima consulta'),
                      _CampoData(
                        valor: _proximaConsulta,
                        dica: 'Escolher data (opcional)',
                        onEscolher: () async {
                          final data = await _escolherData(
                            atual: _proximaConsulta,
                            titulo: 'Próxima consulta',
                          );
                          if (data != null) {
                            setState(() => _proximaConsulta = data);
                          }
                        },
                      ),

                      // ---------------- Notas e anexos ----------------
                      const SizedBox(height: 16),
                      _rotulo('Notas para o laboratório'),
                      TextFormField(
                        controller: _notasController,
                        maxLines: 4,
                        style: _estiloTexto,
                        decoration: _decoracao(
                          'Indicações clínicas, cor e observações...',
                          null,
                        ),
                      ),
                      const SizedBox(height: 16),
                      _buildAnexos(),
                      const SizedBox(height: 24),
                      _buildBotaoSubmeter(),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Partes do formulário
  // ---------------------------------------------------------------------------

  static const _estiloTexto = TextStyle(color: AppColors.portalTextPrimary);

  Widget _buildAvisoSemEnvio() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.portalCardDark,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.portalBorderSubtle),
      ),
      child: const Row(
        children: [
          Icon(Icons.info_outline, color: AppColors.portalGold, size: 18),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Pré-visualização: o envio de pedidos ainda não está '
              'disponível na API.',
              style: TextStyle(
                color: AppColors.portalDescriptionText,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// "Materiais necessários" como no Figma: escreve-se o material,
  /// carrega-se em "Adicionar" e ele aparece como etiqueta com ×.
  /// É um FormField para entrar no validate() (pelo menos 1 material).
  Widget _buildMateriais() {
    return FormField<List<String>>(
      key: _kMateriais,
      validator: (_) => _materiais.isEmpty
          ? 'Adicione pelo menos um material necessário.'
          : null,
      builder: (campo) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _materialController,
                  style: _estiloTexto,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _adicionarMaterial(),
                  decoration:
                      _decoracao(
                        'Escreva o material',
                        Icons.inventory_2_outlined,
                      ).copyWith(
                        enabledBorder: _borda(
                          campo.hasError
                              ? Colors.redAccent
                              : AppColors.portalBorderLight,
                        ),
                      ),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                height: 48,
                child: OutlinedButton(
                  onPressed: _adicionarMaterial,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.portalGold,
                    side: const BorderSide(color: AppColors.portalGold),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text('Adicionar'),
                ),
              ),
            ],
          ),
          if (_materiais.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final material in _materiais)
                  InputChip(
                    avatar: const Icon(
                      Icons.inventory_2_outlined,
                      size: 14,
                      color: AppColors.portalGold,
                    ),
                    label: Text(material),
                    labelStyle: const TextStyle(
                      color: AppColors.portalTextPrimary,
                      fontSize: 12,
                    ),
                    backgroundColor: AppColors.portalSurfaceDark,
                    side: const BorderSide(color: AppColors.portalBorderLight),
                    deleteIconColor: AppColors.portalTextMuted,
                    deleteButtonTooltipMessage: 'Remover $material',
                    onDeleted: () => _removerMaterial(material),
                  ),
              ],
            ),
          ],
          if (campo.hasError) _TextoErro(campo.errorText!),
        ],
      ),
    );
  }

  /// Fotografias e ficheiro STL (como no Figma). Ainda sem envio:
  /// tocar mostra um aviso, porque a API não tem endpoint para ficheiros.
  Widget _buildAnexos() {
    return Row(
      children: [
        Expanded(
          child: _CartaoAnexo(
            icone: Icons.photo_camera_outlined,
            titulo: 'Fotografias',
            descricao: 'JPG / PNG',
            onTap: _anexoIndisponivel,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _CartaoAnexo(
            icone: Icons.description_outlined,
            titulo: 'Ficheiro STL',
            descricao: 'Digital',
            onTap: _anexoIndisponivel,
          ),
        ),
      ],
    );
  }

  Widget _tituloSecao(String texto) {
    return Padding(
      padding: const EdgeInsets.only(top: 22, bottom: 10),
      child: Text(
        texto,
        style: const TextStyle(
          color: AppColors.portalGold,
          fontSize: 11,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.4,
        ),
      ),
    );
  }

  Widget _rotulo(String texto) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        texto,
        style: const TextStyle(
          color: AppColors.portalTextSecondary,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  InputDecoration _decoracao(String dica, IconData? icone) {
    return InputDecoration(
      hintText: dica,
      hintStyle: const TextStyle(
        color: AppColors.portalTextMuted,
        fontSize: 13,
      ),
      filled: true,
      fillColor: AppColors.portalSurfaceDark,
      prefixIcon: icone == null
          ? null
          : Icon(icone, color: AppColors.portalTextMuted, size: 18),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      enabledBorder: _borda(AppColors.portalBorderLight),
      focusedBorder: _borda(AppColors.portalGold),
      errorBorder: _borda(Colors.redAccent),
      focusedErrorBorder: _borda(Colors.redAccent),
    );
  }

  static OutlineInputBorder _borda(Color cor) {
    return OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: BorderSide(color: cor),
    );
  }

  // ---------------------------------------------------------------------------
  // Odontograma
  // ---------------------------------------------------------------------------

  Widget _buildOdontograma() {
    final selecionados = _dentes.toList()..sort();
    // Ecrã estreito (telemóvel): cada arcada passa a ter 2 linhas de 8 dentes.
    final estreito = MediaQuery.sizeOf(context).width < _larguraEcraEstreito;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.portalCardDark,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.portalBorderSubtle),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'ODONTOGRAMA · OPCIONAL',
                  style: TextStyle(
                    color: AppColors.portalGold,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                  ),
                ),
              ),
              if (_dentes.isNotEmpty)
                TextButton(
                  onPressed: _limparDentes,
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.portalTextMuted,
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    minimumSize: const Size(0, 32),
                  ),
                  child: const Text('Limpar', style: TextStyle(fontSize: 12)),
                ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Selecione dentes apenas quando forem relevantes (FDI).',
            style: TextStyle(color: AppColors.portalTextMuted, fontSize: 12),
          ),
          const SizedBox(height: 14),
          if (estreito) ...[
            _buildArcadaEstreita(
              'Arcada superior',
              _superiorDireito,
              _superiorEsquerdo,
              quadranteDireito: 1,
              quadranteEsquerdo: 2,
            ),
            const Divider(color: AppColors.portalBorderLight, height: 24),
            _buildArcadaEstreita(
              'Arcada inferior',
              _inferiorDireito,
              _inferiorEsquerdo,
              quadranteDireito: 4,
              quadranteEsquerdo: 3,
            ),
          ] else ...[
            _buildLegendaLados(),
            const SizedBox(height: 6),
            _buildArcadaLarga('Superior', _superiorDireito, _superiorEsquerdo),
            const Divider(color: AppColors.portalBorderLight, height: 20),
            _buildArcadaLarga('Inferior', _inferiorDireito, _inferiorEsquerdo),
          ],
          const SizedBox(height: 14),
          Row(
            children: [
              _botaoArcada('Arcada superior', const [
                ..._superiorDireito,
                ..._superiorEsquerdo,
              ]),
              const SizedBox(width: 8),
              _botaoArcada('Arcada inferior', const [
                ..._inferiorDireito,
                ..._inferiorEsquerdo,
              ]),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            selecionados.isEmpty
                ? '0 selecionados'
                : '${selecionados.length} '
                      '${selecionados.length == 1 ? 'selecionado' : 'selecionados'}: '
                      '${selecionados.join(', ')}',
            style: TextStyle(
              color: selecionados.isEmpty
                  ? AppColors.portalTextMuted
                  : AppColors.portalTextPrimary,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegendaLados() {
    const estilo = TextStyle(
      color: AppColors.portalTimestampText,
      fontSize: 10,
    );
    return const Row(
      children: [
        Expanded(child: Text('← Direita do paciente', style: estilo)),
        Text('Esquerda do paciente →', style: estilo),
      ],
    );
  }

  /// Ecrã largo (≥ 600 px): cada arcada numa só linha de 16 dentes,
  /// com o separador da linha média ao centro.
  Widget _buildArcadaLarga(String nome, List<int> direito, List<int> esquerdo) {
    return Column(
      children: [
        Text(
          nome,
          style: const TextStyle(
            color: AppColors.portalTextMuted,
            fontSize: 10,
          ),
        ),
        const SizedBox(height: 4),
        Row(
          children: [
            for (final dente in direito) _denteLargo(dente),
            _separadorLinhaMedia(),
            for (final dente in esquerdo) _denteLargo(dente),
          ],
        ),
      ],
    );
  }

  /// Ecrã estreito (< 600 px): a arcada é partida em 2 linhas de 8 dentes —
  /// primeiro o lado direito do paciente, depois o esquerdo — mantendo a
  /// ordem FDI (do siso para a linha média, e da linha média para o siso).
  Widget _buildArcadaEstreita(
    String nome,
    List<int> direito,
    List<int> esquerdo, {
    required int quadranteDireito,
    required int quadranteEsquerdo,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          nome.toUpperCase(),
          style: const TextStyle(
            color: AppColors.portalTextSecondary,
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
          ),
        ),
        const SizedBox(height: 8),
        _linhaQuadrante(
          'Direita do paciente · Q$quadranteDireito',
          'linha média →',
          direito,
        ),
        const SizedBox(height: 10),
        _linhaQuadrante(
          'Esquerda do paciente · Q$quadranteEsquerdo',
          '← linha média',
          esquerdo,
          linhaMediaAEsquerda: true,
        ),
      ],
    );
  }

  /// Uma linha com os 8 dentes de um quadrante.
  /// O LayoutBuilder calcula o tamanho de cada dente a partir da largura
  /// disponível, mas nunca abaixo de 32 px. Se o ecrã for tão estreito que
  /// nem assim cabe, a linha faz scroll horizontal (em vez de dar erro).
  Widget _linhaQuadrante(
    String titulo,
    String indicacaoLinhaMedia,
    List<int> dentes, {
    bool linhaMediaAEsquerda = false,
  }) {
    const espaco = 4.0;
    const estiloLegenda = TextStyle(
      color: AppColors.portalTimestampText,
      fontSize: 10,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: Text(titulo, style: estiloLegenda)),
            Text(indicacaoLinhaMedia, style: estiloLegenda),
          ],
        ),
        const SizedBox(height: 4),
        LayoutBuilder(
          builder: (context, constraints) {
            final larguraLivre =
                constraints.maxWidth - espaco * (dentes.length - 1);
            final tamanho = (larguraLivre / dentes.length).clamp(
              _tamanhoMinimoDente,
              56.0,
            );
            return SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (var i = 0; i < dentes.length; i++) ...[
                    if (i > 0) const SizedBox(width: espaco),
                    SizedBox(
                      width: tamanho,
                      height: tamanho < 40 ? 40 : tamanho,
                      child: _buildDente(dentes[i]),
                    ),
                  ],
                ],
              ),
            );
          },
        ),
        // Pequena barra dourada a marcar o lado da linha média.
        Align(
          alignment: linhaMediaAEsquerda
              ? Alignment.centerLeft
              : Alignment.centerRight,
          child: Container(
            margin: const EdgeInsets.only(top: 4),
            width: 24,
            height: 2,
            color: AppColors.portalGold.withValues(alpha: 0.5),
          ),
        ),
      ],
    );
  }

  Widget _separadorLinhaMedia() {
    return Container(
      width: 2,
      height: 40,
      margin: const EdgeInsets.symmetric(horizontal: 3),
      color: AppColors.portalGold.withValues(alpha: 0.4),
    );
  }

  /// No modo largo os dentes dividem a linha (Expanded) com 1 px de espaço.
  Widget _denteLargo(int dente) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 1),
        child: _buildDente(dente),
      ),
    );
  }

  /// Um dente: tocar seleciona / desseleciona.
  /// Ocupa todo o espaço que lhe derem — no modo estreito são ≥ 32 px.
  Widget _buildDente(int dente) {
    final selecionado = _dentes.contains(dente);
    return Semantics(
      button: true,
      selected: selecionado,
      label: 'Dente $dente',
      child: InkWell(
        onTap: () => _alternarDente(dente),
        borderRadius: BorderRadius.circular(8),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          height: 40,
          decoration: BoxDecoration(
            color: selecionado
                ? AppColors.portalGold
                : AppColors.portalSurfaceDark,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: selecionado
                  ? AppColors.portalGold
                  : AppColors.portalBorderLight,
            ),
          ),
          alignment: Alignment.center,
          child: FittedBox(
            fit: BoxFit.scaleDown,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2),
              child: Text(
                '$dente',
                style: TextStyle(
                  color: selecionado
                      ? AppColors.portalTextOnAccent
                      : AppColors.portalTextSecondary,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _botaoArcada(String texto, List<int> dentes) {
    final todos = dentes.every(_dentes.contains);
    return Expanded(
      child: OutlinedButton(
        onPressed: () => _selecionarArcada(dentes),
        style: OutlinedButton.styleFrom(
          foregroundColor: todos
              ? AppColors.portalGold
              : AppColors.portalTextSecondary,
          side: BorderSide(
            color: todos ? AppColors.portalGold : AppColors.portalBorderLight,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(fontSize: 12),
        ),
        child: Text(texto),
      ),
    );
  }

  Widget _buildBotaoSubmeter() {
    return InkWell(
      onTap: _submeter,
      borderRadius: BorderRadius.circular(12),
      child: Ink(
        padding: const EdgeInsets.symmetric(vertical: 15),
        decoration: BoxDecoration(
          color: AppColors.portalGold,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Submeter pedido',
              style: TextStyle(
                color: AppColors.portalTextOnAccent,
                fontWeight: FontWeight.w700,
                fontSize: 14,
              ),
            ),
            SizedBox(width: 8),
            Icon(Icons.arrow_forward, color: AppColors.portalTextOnAccent),
          ],
        ),
      ),
    );
  }
}

// =============================================================================
// Componentes do formulário
// =============================================================================

/// Grupo de botões de escolha única (ex.: Fluxo Físico / Digital),
/// como o "segment" do Figma. Há sempre uma opção escolhida.
class _CampoOpcoes extends StatelessWidget {
  const _CampoOpcoes({
    required this.opcoes,
    required this.valor,
    required this.onChanged,
    this.icones,
  });

  final List<String> opcoes;
  final String valor;
  final ValueChanged<String> onChanged;
  final List<IconData>? icones;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (var i = 0; i < opcoes.length; i++) ...[
          if (i > 0) const SizedBox(width: 8),
          Expanded(
            child: _botao(opcoes[i], icones == null ? null : icones![i]),
          ),
        ],
      ],
    );
  }

  Widget _botao(String opcao, IconData? icone) {
    final selecionado = valor == opcao;
    final cor = selecionado ? AppColors.portalGold : AppColors.portalTextMuted;
    return Semantics(
      button: true,
      selected: selecionado,
      child: InkWell(
        onTap: () => onChanged(opcao),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 6),
          decoration: BoxDecoration(
            color: selecionado
                ? AppColors.portalGold.withValues(alpha: 0.12)
                : AppColors.portalSurfaceDark,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: selecionado
                  ? AppColors.portalGold
                  : AppColors.portalBorderLight,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (icone != null) ...[
                Icon(icone, size: 18, color: cor),
                const SizedBox(width: 6),
              ],
              Flexible(
                child: Text(
                  opcao,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: selecionado
                        ? AppColors.portalGold
                        : AppColors.portalTextSecondary,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Campo de data (opcional) que abre o calendário.
class _CampoData extends StatelessWidget {
  const _CampoData({
    required this.valor,
    required this.dica,
    required this.onEscolher,
  });

  final DateTime? valor;
  final String dica;
  final Future<void> Function() onEscolher;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onEscolher,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
        decoration: BoxDecoration(
          color: AppColors.portalSurfaceDark,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.portalBorderLight),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.event_outlined,
              color: AppColors.portalTextMuted,
              size: 18,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                valor == null ? dica : formatarData(valor),
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: valor == null
                      ? AppColors.portalTextMuted
                      : AppColors.portalTextPrimary,
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Cartão de anexo (Fotografias / Ficheiro STL), como no Figma.
class _CartaoAnexo extends StatelessWidget {
  const _CartaoAnexo({
    required this.icone,
    required this.titulo,
    required this.descricao,
    required this.onTap,
  });

  final IconData icone;
  final String titulo;
  final String descricao;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 10),
        decoration: BoxDecoration(
          color: AppColors.portalSurfaceDark,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.portalBorderLight),
        ),
        child: Column(
          children: [
            Icon(icone, color: AppColors.portalGold),
            const SizedBox(height: 6),
            Text(
              titulo,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.portalTextPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              descricao,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.portalTextMuted,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Mensagem de erro vermelha (igual à dos TextFormField).
class _TextoErro extends StatelessWidget {
  const _TextoErro(this.texto);

  final String texto;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 12, top: 6),
      child: Text(
        texto,
        style: const TextStyle(color: Colors.redAccent, fontSize: 12),
      ),
    );
  }
}
