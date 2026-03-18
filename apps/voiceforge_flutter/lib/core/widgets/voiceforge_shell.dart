import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_gradients.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';
import '../../app/design_system/app_typography.dart';
import 'vf_chip.dart';
import 'vf_panel.dart';

class VoiceForgeShell extends StatelessWidget {
  const VoiceForgeShell({
    super.key,
    required this.currentLocation,
    required this.child,
  });

  final String currentLocation;
  final Widget child;

  static const _destinations = [
    _ShellDestination(
      label: 'Resumen',
      icon: Icons.space_dashboard_outlined,
      route: '/',
      subtitle: 'Estado general de tu espacio',
    ),
    _ShellDestination(
      label: 'Voces',
      icon: Icons.library_music_outlined,
      route: '/voices',
      subtitle: 'Biblioteca de identidades vocales',
    ),
    _ShellDestination(
      label: 'Convertir',
      icon: Icons.auto_awesome_motion_outlined,
      route: '/conversions/create',
      subtitle: 'Crea una conversión offline',
    ),
    _ShellDestination(
      label: 'Historial',
      icon: Icons.history_outlined,
      route: '/conversions/history',
      subtitle: 'Revisa tus resultados recientes',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.sizeOf(context).width >= 1040;

    return Scaffold(
      backgroundColor: AppColors.bg950,
      body: DecoratedBox(
        decoration: BoxDecoration(
          color: AppColors.bg950,
          gradient: AppGradients.hero,
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: AppGradients.glow(
                      alignment: const Alignment(0.9, -0.95),
                      color: AppColors.primary500,
                      opacity: 0.22,
                    ),
                  ),
                ),
              ),
            ),
            Positioned(
              left: -120,
              bottom: -180,
              width: 420,
              height: 420,
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: AppGradients.glow(
                      alignment: Alignment.center,
                      color: AppColors.accentCyan,
                      opacity: 0.14,
                    ),
                  ),
                ),
              ),
            ),
            SafeArea(
              child: Row(
                children: [
                  if (isWide)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 20, 0, 20),
                      child: _DesktopRail(currentLocation: currentLocation),
                    ),
                  Expanded(
                    child: Column(
                      children: [
                        _TopBar(
                          currentLocation: currentLocation,
                          isWide: isWide,
                        ),
                        Expanded(child: child),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: isWide
          ? null
          : NavigationBar(
              height: 78,
              selectedIndex: _selectedIndex(currentLocation),
              destinations: _destinations
                  .map(
                    (destination) => NavigationDestination(
                      icon: Icon(destination.icon),
                      label: destination.label,
                    ),
                  )
                  .toList(),
              onDestinationSelected: (index) =>
                  context.go(_destinations[index].route),
            ),
    );
  }

  static int _selectedIndex(String currentLocation) {
    for (var index = 0; index < _destinations.length; index++) {
      if (currentLocation == _destinations[index].route ||
          currentLocation.startsWith('${_destinations[index].route}/')) {
        return index;
      }
    }
    return 0;
  }
}

class _DesktopRail extends StatelessWidget {
  const _DesktopRail({required this.currentLocation});

  final String currentLocation;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 292,
      child: VFPanel(
        variant: VFPanelVariant.subdued,
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _BrandHeader(),
            const SizedBox(height: AppSpacing.xxl),
            ...VoiceForgeShell._destinations.map(
              (destination) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: _RailButton(
                  destination: destination,
                  selected:
                      currentLocation == destination.route ||
                      currentLocation.startsWith('${destination.route}/'),
                ),
              ),
            ),
            const Spacer(),
            VFPanel(
              variant: VFPanelVariant.hero,
              padding: const EdgeInsets.all(AppSpacing.lg),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFF1A2346),
                  Color(0xFF121C35),
                  Color(0xFF15274A),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const VFChip(
                    label: 'Studio mode',
                    tone: VFChipTone.recommended,
                    icon: Icons.workspace_premium_outlined,
                  ),
                  const SizedBox(height: AppSpacing.md),
                  Text(
                    'Calidad lista para producción',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    'Prioriza voces guardadas, resultados limpios y una experiencia consistente entre Android y Web.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BrandHeader extends StatelessWidget {
  const _BrandHeader();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            gradient: AppGradients.premium,
            borderRadius: AppRadius.lg,
            boxShadow: const [
              BoxShadow(
                color: Color(0x246D7CFF),
                blurRadius: 18,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: const Icon(Icons.graphic_eq_rounded, color: AppColors.text100),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'VoiceForge',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: AppSpacing.xxs),
              Text(
                'Voice conversion multiplataforma',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _RailButton extends StatefulWidget {
  const _RailButton({required this.destination, required this.selected});

  final _ShellDestination destination;
  final bool selected;

  @override
  State<_RailButton> createState() => _RailButtonState();
}

class _RailButtonState extends State<_RailButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final selected = widget.selected;
    final active = selected || _hovered;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 160),
      curve: Curves.easeOutCubic,
      decoration: BoxDecoration(
        color: selected
            ? AppColors.primary500.withValues(alpha: 0.16)
            : Colors.transparent,
        borderRadius: AppRadius.lg,
        border: Border.all(
          color: active ? AppColors.borderStrong : Colors.transparent,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => context.go(widget.destination.route),
          borderRadius: AppRadius.lg,
          onHover: (value) => setState(() => _hovered = value),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: AppSpacing.md,
            ),
            child: Row(
              children: [
                Icon(
                  widget.destination.icon,
                  color: selected ? AppColors.primary400 : AppColors.text300,
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.destination.label,
                        style: AppTypography.labelLarge.copyWith(
                          color: selected
                              ? AppColors.text100
                              : AppColors.text300,
                        ),
                      ),
                      const SizedBox(height: AppSpacing.xxs),
                      Text(
                        widget.destination.subtitle,
                        style: AppTypography.caption.copyWith(
                          color: selected
                              ? AppColors.text300
                              : AppColors.text500,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.currentLocation, required this.isWide});

  final String currentLocation;
  final bool isWide;

  @override
  Widget build(BuildContext context) {
    final page = _pageMeta(currentLocation);
    return Padding(
      padding: EdgeInsets.fromLTRB(
        isWide ? AppSpacing.xxl : AppSpacing.md,
        AppSpacing.lg,
        isWide ? AppSpacing.xxl : AppSpacing.md,
        AppSpacing.md,
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  page.title,
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: AppSpacing.xxs),
                Text(
                  page.subtitle,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.lg),
          if (isWide)
            const VFChip(
              label: 'Equilibrado recomendado',
              tone: VFChipTone.recommended,
              icon: Icons.stars_outlined,
            ),
        ],
      ),
    );
  }

  _PageMeta _pageMeta(String location) {
    if (location.startsWith('/voices')) {
      return const _PageMeta(
        title: 'Voces guardadas',
        subtitle:
            'Gestiona muestras, identidad vocal y preparación de cada perfil.',
      );
    }
    if (location.startsWith('/conversions/create')) {
      return const _PageMeta(
        title: 'Crear conversión',
        subtitle:
            'Elige una voz objetivo y prepara un resultado offline con foco en claridad.',
      );
    }
    if (location.startsWith('/conversions/history')) {
      return const _PageMeta(
        title: 'Historial',
        subtitle:
            'Revisa tus resultados recientes y vuelve a abrirlos cuando lo necesites.',
      );
    }
    return const _PageMeta(
      title: 'Resumen',
      subtitle:
          'Tu espacio de trabajo con foco en voces, resultados y acciones prioritarias.',
    );
  }
}

class _ShellDestination {
  const _ShellDestination({
    required this.label,
    required this.icon,
    required this.route,
    required this.subtitle,
  });

  final String label;
  final IconData icon;
  final String route;
  final String subtitle;
}

class _PageMeta {
  const _PageMeta({required this.title, required this.subtitle});

  final String title;
  final String subtitle;
}
