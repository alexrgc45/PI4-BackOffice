import 'package:material_ui/material_ui.dart';

import 'cliente/detalhe_pedido.dart';
import 'cliente/notificacoes_cliente.dart';
import 'cliente/novo_pedido.dart';
import 'cliente/os_meus_pedidos.dart';
import 'cliente/pagina_principal.dart';
import 'route_names.dart';
import 'screens/home_admin.dart';
import 'screens/login_screen.dart';
import 'screens/pagina_principal.dart';

class AppRoutes {
  static const String homePath = AppRouteNames.homePath;
  static const String loginPath = AppRouteNames.loginPath;
  static const String mainPath = AppRouteNames.mainPath;
  static const String adminPath = AppRouteNames.adminPath;
  static const String clientPath = AppRouteNames.clientPath;

  static final Map<String, WidgetBuilder> routes = {
    homePath: (context) => const PaginaPrincipal(),
    loginPath: (context) => const LoginScreen(),
    mainPath: (context) => const PaginaPrincipal(),
    adminPath: (context) => const HomeAdminPage(),
    clientPath: (context) => const PortalClinicaPage(),
    AppRouteNames.clientPedidosPath: (context) => const OsMeusPedidosPage(),
    AppRouteNames.clientPedidoDetalhePath: (context) {
      final argument = ModalRoute.of(context)?.settings.arguments;
      return DetalhePedidoPage(trabalhoId: argument is int ? argument : 0);
    },
    AppRouteNames.clientNotificacoesPath: (context) =>
        const NotificacoesClientePage(),
    AppRouteNames.clientNovoPedidoPath: (context) => const NovoPedidoPage(),
  };
}
