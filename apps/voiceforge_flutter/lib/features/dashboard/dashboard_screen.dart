import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_gradients.dart';
import '../../app/design_system/app_spacing.dart';
import '../../core/models/conversion_models.dart';
import '../../core/models/voice_models.dart';
import '../../core/utils/formatters.dart';
import '../../core/voiceforge_scope.dart';
import '../../core/widgets/vf_button.dart';
import '../../core/widgets/vf_card.dart';
import '../../core/widgets/vf_chip.dart';
import '../../core/widgets/vf_empty_state.dart';
import '../../core/widgets/vf_page_scaffold.dart';
import '../../core/widgets/vf_panel.dart';
import '../../core/widgets/vf_progress_bar.dart';
import '../../core/widgets/vf_section_header.dart';
import '../../core/widgets/vf_state_panel.dart';
import '../../core/widgets/vf_status_badge.dart';
import '../../core/widgets/vf_waveform_container.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<_DashboardData> _dashboardFuture;

  @override
  void initState() {
    super.initState();
    _dashboardFuture = _loadDashboard();
  }

  Future<_DashboardData> _loadDashboard() async {
    final scope = VoiceForgeScope.read(context);
    final profiles = await scope.voiceRepository.listProfiles();
    final jobs = await scope.conversionRepository.listJobs();
    profiles.sort((a, b) => b.readinessScore.compareTo(a.readinessScore));
    jobs.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return _DashboardData(profiles: profiles, jobs: jobs);
  }

  Future<void> _refresh() async {
    setState(() {
      _dashboardFuture = _loadDashboard();
    });
  }

  @override
  Widget build(BuildContext context) {
    final session = VoiceForgeScope.of(context).notifier!;
    if (!session.isAuthenticated) {
      return VFPageScaffold(
        children: [
          VFStatePanel(
            icon: Icons.lock_outline_rounded,
            title: 'Inicia sesión para ver tu resumen',
            subtitle:
                'El dashboard ya consume perfiles y conversiones reales desde el backend.',
            actionLabel: 'Volver al acceso',
            onAction: () => context.go('/login'),
          ),
        ],
      );
    }

    return FutureBuilder<_DashboardData>(
      future: _dashboardFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.space_dashboard_outlined,
                title: 'Cargando tu resumen',
                subtitle:
                    'Estamos consultando perfiles, muestras y conversiones recientes.',
                isLoading: true,
              ),
            ],
          );
        }

        if (snapshot.hasError) {
          return VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.error_outline,
                title: 'No pudimos cargar el resumen',
                subtitle:
                    'Revisa la conexión con el backend e inténtalo de nuevo.',
                actionLabel: 'Reintentar',
                onAction: _refresh,
              ),
            ],
          );
        }

        final data = snapshot.data!;
        final profiles = data.profiles;
        final jobs = data.jobs;
        final strongestProfile = profiles.isEmpty ? null : profiles.first;
        final latestJob = jobs.isEmpty ? null : jobs.first;
        final totalSamples = profiles.fold<int>(0, (sum, profile) => sum + profile.clipCount);

        return VFPageScaffold(
          children: [
            VFPanel(
              variant: VFPanelVariant.hero,
              gradient: AppGradients.hero,
              padding: const EdgeInsets.all(AppSpacing.xxl),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final compact = constraints.maxWidth < 860;
                  final copy = Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      VFChip(
                        label: session.currentUser?.displayName ?? 'VoiceForge',
                        tone: VFChipTone.recommended,
                        icon: Icons.workspace_premium_outlined,
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Text(
                        'Convierte audio con una identidad vocal clara, consistente y lista para entrega.',
                        style: Theme.of(context)
                            .textTheme
                            .displaySmall
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: AppSpacing.md),
                      Text(
                        profiles.isEmpty
                            ? 'Empieza creando un perfil de voz y subiendo tus primeras muestras para activar el flujo completo.'
                            : 'Tu espacio ya refleja datos reales del backend: voces guardadas, material disponible y resultados recientes.',
                        style: Theme.of(context)
                            .textTheme
                            .bodyLarge
                            ?.copyWith(color: AppColors.text300),
                      ),
                      const SizedBox(height: AppSpacing.xl),
                      Wrap(
                        spacing: AppSpacing.md,
                        runSpacing: AppSpacing.md,
                        children: [
                          VFButton(
                            label: 'Crear conversión',
                            size: VFButtonSize.lg,
                            leadingIcon: Icons.auto_awesome_motion_outlined,
                            onPressed: profiles.isEmpty
                                ? null
                                : () => context.go('/conversions/create'),
                          ),
                          VFButton(
                            label: 'Ver voces',
                            variant: VFButtonVariant.secondary,
                            size: VFButtonSize.lg,
                            leadingIcon: Icons.library_music_outlined,
                            onPressed: () => context.go('/voices'),
                          ),
                        ],
                      ),
                    ],
                  );

                  final side = Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      VFWaveformContainer(
                        title: 'Actividad reciente',
                        caption: latestJob == null
                            ? 'Aún no hay resultados, pero el flujo ya está listo para crear tu primera conversión.'
                            : 'Tu último trabajo aparece aquí con estado y acceso al historial.',
                        trailing: VFStatusBadge.fromStatus(
                          formatStatusLabel(latestJob?.status ?? 'pending'),
                        ),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      VFPanel(
                        variant: VFPanelVariant.subdued,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Siguiente mejora recomendada',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: AppSpacing.xs),
                            Text(
                              strongestProfile == null
                                  ? 'Crea un perfil para empezar a organizar tu biblioteca.'
                                  : readinessHint(
                                      score: strongestProfile.readinessScore,
                                      clipCount: strongestProfile.clipCount,
                                    ),
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                          ],
                        ),
                      ),
                    ],
                  );

                  if (compact) {
                    return Column(
                      children: [
                        copy,
                        const SizedBox(height: AppSpacing.xl),
                        side,
                      ],
                    );
                  }

                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(flex: 6, child: copy),
                      const SizedBox(width: AppSpacing.xl),
                      Expanded(flex: 5, child: side),
                    ],
                  );
                },
              ),
            ),
            Wrap(
              spacing: AppSpacing.md,
              runSpacing: AppSpacing.md,
              children: [
                _MetricCard(
                  label: 'Voces guardadas',
                  value: '${profiles.length}',
                  caption: 'Gestiona varias identidades vocales por usuario.',
                ),
                _MetricCard(
                  label: 'Perfil más sólido',
                  value: strongestProfile == null
                      ? 'Sin datos'
                      : '${strongestProfile.readinessScore.toInt()}%',
                  caption: strongestProfile == null
                      ? 'Crea tu primer perfil para activar el resumen.'
                      : '${strongestProfile.name} es tu mejor punto de partida.',
                ),
                _MetricCard(
                  label: 'Resultados activos',
                  value: '${jobs.length}',
                  caption: 'Tus últimos trabajos siguen disponibles para revisar.',
                ),
                _MetricCard(
                  label: 'Muestras disponibles',
                  value: '$totalSamples',
                  caption: 'Más cobertura suele traducirse en mejor identidad vocal.',
                ),
              ],
            ),
            LayoutBuilder(
              builder: (context, constraints) {
                final compact = constraints.maxWidth < 980;
                final profilesPanel = VFCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const VFSectionHeader(
                        title: 'Perfiles destacados',
                        subtitle:
                            'Revisa cuáles están mejor preparados para una conversión estable.',
                      ),
                      const SizedBox(height: AppSpacing.xl),
                      if (profiles.isEmpty)
                        const VFEmptyState(
                          icon: Icons.library_music_outlined,
                          title: 'Todavía no hay perfiles',
                          subtitle:
                              'Ve a la biblioteca para crear tu primer perfil y empezar a subir muestras.',
                        )
                      else
                        ...profiles.take(3).map(
                              (profile) => Padding(
                                padding: const EdgeInsets.only(
                                  bottom: AppSpacing.lg,
                                ),
                                child: _VoiceReadinessTile(profile: profile),
                              ),
                            ),
                    ],
                  ),
                );

                final actions = Column(
                  children: [
                    const _QuickActionPanel(),
                    const SizedBox(height: AppSpacing.md),
                    _ResultOverviewPanel(job: latestJob),
                  ],
                );

                if (compact) {
                  return Column(
                    children: [
                      profilesPanel,
                      const SizedBox(height: AppSpacing.md),
                      actions,
                    ],
                  );
                }

                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(flex: 6, child: profilesPanel),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(flex: 5, child: actions),
                  ],
                );
              },
            ),
          ],
        );
      },
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.value,
    required this.caption,
  });

  final String label;
  final String value;
  final String caption;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 270,
      child: VFCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: Theme.of(context).textTheme.labelMedium),
            const SizedBox(height: AppSpacing.lg),
            Text(
              value,
              style: Theme.of(context)
                  .textTheme
                  .displaySmall
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(caption, style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}

class _VoiceReadinessTile extends StatelessWidget {
  const _VoiceReadinessTile({required this.profile});

  final VoiceProfile profile;

  @override
  Widget build(BuildContext context) {
    return VFCard(
      variant: VFCardVariant.interactive,
      padding: const EdgeInsets.all(AppSpacing.lg),
      onTap: () => context.go('/voices/${profile.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  profile.name,
                  style: Theme.of(context)
                      .textTheme
                      .titleLarge
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
              ),
              VFStatusBadge.fromStatus(formatStatusLabel(profile.status)),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            '${profile.clipCount} muestras  •  ${formatDurationSeconds(profile.totalDurationSeconds)}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: AppSpacing.md),
          VFProgressBar(
            value: profile.readinessScore / 100,
            label: readinessHeadline(profile.readinessScore),
            trailing: '${profile.readinessScore.toInt()}%',
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            readinessHint(
              score: profile.readinessScore,
              clipCount: profile.clipCount,
            ),
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

class _QuickActionPanel extends StatelessWidget {
  const _QuickActionPanel();

  @override
  Widget build(BuildContext context) {
    return VFCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const VFSectionHeader(
            title: 'Acciones rápidas',
            subtitle: 'Mantén el flujo claro en móvil y escritorio.',
          ),
          const SizedBox(height: AppSpacing.xl),
          VFButton(
            label: 'Crear conversión',
            expand: true,
            size: VFButtonSize.lg,
            leadingIcon: Icons.auto_awesome_motion_outlined,
            onPressed: () => context.go('/conversions/create'),
          ),
          const SizedBox(height: AppSpacing.md),
          VFButton(
            label: 'Añadir muestra',
            expand: true,
            variant: VFButtonVariant.secondary,
            leadingIcon: Icons.upload_file_outlined,
            onPressed: () => context.go('/voices'),
          ),
          const SizedBox(height: AppSpacing.md),
          VFButton(
            label: 'Ver historial',
            expand: true,
            variant: VFButtonVariant.ghost,
            trailingIcon: Icons.arrow_forward_rounded,
            onPressed: () => context.go('/conversions/history'),
          ),
        ],
      ),
    );
  }
}

class _ResultOverviewPanel extends StatelessWidget {
  const _ResultOverviewPanel({required this.job});

  final ConversionJob? job;

  @override
  Widget build(BuildContext context) {
    return VFPanel(
      variant: VFPanelVariant.subdued,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const VFSectionHeader(
            title: 'Último resultado',
            subtitle: 'Tu resultado más reciente queda a un paso de revisión.',
          ),
          const SizedBox(height: AppSpacing.lg),
          if (job == null)
            const VFEmptyState(
              icon: Icons.history_outlined,
              title: 'Aún no hay resultados',
              subtitle:
                  'Cuando crees tu primera conversión, este panel mostrará su estado y acceso directo.',
            )
          else ...[
            VFWaveformContainer(
              height: 150,
              title: formatModeLabel(job!.mode),
              caption:
                  'Estado actual: ${formatStatusLabel(job!.status)}. Fuente: ${job!.sourceAudioFilename}',
            ),
            const SizedBox(height: AppSpacing.md),
            VFButton(
              label: 'Abrir historial',
              variant: VFButtonVariant.secondary,
              onPressed: () => context.go('/conversions/history/${job!.id}'),
            ),
          ],
        ],
      ),
    );
  }
}

class _DashboardData {
  const _DashboardData({
    required this.profiles,
    required this.jobs,
  });

  final List<VoiceProfile> profiles;
  final List<ConversionJob> jobs;
}
