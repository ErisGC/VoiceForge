import 'dart:async';
import 'dart:io' as io;
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:just_audio/just_audio.dart' as just_audio;
import 'package:permission_handler/permission_handler.dart' as permission_handler;
import 'package:record/record.dart' as record;

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_gradients.dart';
import '../../app/design_system/app_spacing.dart';
import '../../core/files/audio_file_picker.dart';
import '../../core/files/audio_upload_file.dart';
import '../../core/models/voice_models.dart';
import '../../core/repositories/voice_repository.dart';
import '../../core/utils/formatters.dart';
import '../../core/voiceforge_scope.dart';
import '../../core/widgets/vf_button.dart';
import '../../core/widgets/vf_card.dart';
import '../../core/widgets/vf_chip.dart';
import '../../core/widgets/vf_empty_state.dart';
import '../../core/widgets/vf_input.dart';
import '../../core/widgets/vf_page_scaffold.dart';
import '../../core/widgets/vf_panel.dart';
import '../../core/widgets/vf_progress_bar.dart';
import '../../core/widgets/vf_section_header.dart';
import '../../core/widgets/vf_state_panel.dart';
import '../../core/widgets/vf_status_badge.dart';
import '../../core/widgets/vf_waveform_container.dart';

class VoiceLibraryScreen extends StatefulWidget {
  const VoiceLibraryScreen({super.key});

  @override
  State<VoiceLibraryScreen> createState() => _VoiceLibraryScreenState();
}

class _VoiceLibraryScreenState extends State<VoiceLibraryScreen> {
  late Future<List<VoiceProfile>> _profilesFuture;

  @override
  void initState() {
    super.initState();
    _profilesFuture = _repository.listProfiles();
  }

  VoiceRepository get _repository => VoiceForgeScope.read(context).voiceRepository;

  Future<void> _refresh() async {
    setState(() {
      _profilesFuture = _repository.listProfiles();
    });
  }

  Future<void> _createProfile() async {
    final profile = await showDialog<VoiceProfile>(
      context: context,
      builder: (dialogContext) => _CreateProfileDialog(repository: _repository),
    );
    if (profile == null || !mounted) {
      return;
    }
    await _refresh();
    if (!mounted) {
      return;
    }
    context.go('/voices/${profile.id}');
  }

  @override
  Widget build(BuildContext context) {
    final session = VoiceForgeScope.of(context).notifier!;
    if (!session.isAuthenticated) {
      return VFPageScaffold(
        children: [
          VFStatePanel(
            icon: Icons.lock_outline_rounded,
            title: 'Inicia sesión para ver tus voces',
            subtitle:
                'La biblioteca se conecta al backend real y necesita una sesión activa para cargar tus perfiles.',
            actionLabel: 'Volver al acceso',
            onAction: () => context.go('/login'),
          ),
        ],
      );
    }

    return FutureBuilder<List<VoiceProfile>>(
      future: _profilesFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.library_music_outlined,
                title: 'Cargando tus voces',
                subtitle:
                    'Estamos consultando tus perfiles y su nivel de preparación.',
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
                title: 'No pudimos cargar la biblioteca',
                subtitle: 'Revisa la conexión con el backend e inténtalo de nuevo.',
                actionLabel: 'Reintentar',
                onAction: _refresh,
              ),
            ],
          );
        }

        final profiles = snapshot.data ?? const <VoiceProfile>[];
        if (profiles.isEmpty) {
          return VFPageScaffold(
            children: [
              VFPanel(
                variant: VFPanelVariant.hero,
                gradient: AppGradients.hero,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const VFSectionHeader(
                      eyebrow: 'Biblioteca de voces',
                      title: 'Todavía no tienes perfiles guardados',
                      subtitle:
                          'Crea tu primer perfil para empezar a subir muestras y construir una identidad vocal reutilizable.',
                    ),
                    const SizedBox(height: AppSpacing.xl),
                    VFButton(
                      label: 'Crear primer perfil',
                      leadingIcon: Icons.add_circle_outline,
                      onPressed: _createProfile,
                    ),
                  ],
                ),
              ),
              VFEmptyState(
                icon: Icons.record_voice_over_outlined,
                title: 'Tu biblioteca está vacía',
                subtitle:
                    'Cuando crees un perfil, aquí verás su preparación, sus muestras y el acceso directo para convertir audio.',
                actionLabel: 'Crear perfil',
                onAction: _createProfile,
              ),
            ],
          );
        }

        final strongestVoice = profiles.reduce(
          (current, next) =>
              current.readinessScore >= next.readinessScore ? current : next,
        );
        final totalClips =
            profiles.fold<int>(0, (sum, profile) => sum + profile.clipCount);
        final averageReadiness = profiles.fold<double>(
              0,
              (sum, profile) => sum + profile.readinessScore,
            ) /
            profiles.length;

        return VFPageScaffold(
          children: [
            VFPanel(
              variant: VFPanelVariant.hero,
              gradient: AppGradients.hero,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const VFSectionHeader(
                    eyebrow: 'Biblioteca de voces',
                    title: 'Tus perfiles guardados',
                    subtitle:
                        'Organiza identidades vocales reutilizables, mejora cada perfil con nuevas muestras y mantén claro qué voz está lista para producir resultados consistentes.',
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  Wrap(
                    spacing: AppSpacing.md,
                    runSpacing: AppSpacing.md,
                    children: [
                      _LibraryMetric(
                        label: 'Perfiles activos',
                        value: '${profiles.length}',
                      ),
                      _LibraryMetric(
                        label: 'Perfil más sólido',
                        value: strongestVoice.name,
                      ),
                      _LibraryMetric(
                        label: 'Identidad promedio',
                        value: '${averageReadiness.round()}%',
                      ),
                      _LibraryMetric(
                        label: 'Muestras totales',
                        value: '$totalClips clips',
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  Wrap(
                    spacing: AppSpacing.md,
                    runSpacing: AppSpacing.md,
                    children: [
                      VFButton(
                        label: 'Crear conversión',
                        leadingIcon: Icons.auto_awesome_motion_outlined,
                        onPressed: () => context.go('/conversions/create'),
                      ),
                      VFButton(
                        label: 'Crear perfil',
                        variant: VFButtonVariant.secondary,
                        leadingIcon: Icons.add_circle_outline,
                        onPressed: _createProfile,
                      ),
                    ],
                  ),
                ],
              ),
            ),
            LayoutBuilder(
              builder: (context, constraints) {
                final isWide = constraints.maxWidth >= 980;
                final cardWidth = isWide
                    ? (constraints.maxWidth - AppSpacing.md) / 2
                    : constraints.maxWidth;

                return Wrap(
                  spacing: AppSpacing.md,
                  runSpacing: AppSpacing.md,
                  children: [
                    for (final profile in profiles)
                      SizedBox(
                        width: cardWidth,
                        child: _VoiceLibraryCard(profile: profile),
                      ),
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

class VoiceProfileDetailScreen extends StatefulWidget {
  const VoiceProfileDetailScreen({super.key, required this.voiceId});

  final String voiceId;

  @override
  State<VoiceProfileDetailScreen> createState() =>
      _VoiceProfileDetailScreenState();
}

class _VoiceProfileDetailScreenState extends State<VoiceProfileDetailScreen> {
  late Future<_VoiceDetailData> _detailFuture;

  @override
  void initState() {
    super.initState();
    _detailFuture = _loadDetail();
  }

  VoiceRepository get _repository => VoiceForgeScope.read(context).voiceRepository;

  Future<_VoiceDetailData> _loadDetail() async {
    final profile = await _repository.getProfile(widget.voiceId);
    final samples = await _repository.listSamples(widget.voiceId);
    samples.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return _VoiceDetailData(profile: profile, samples: samples);
  }

  Future<void> _refresh() async {
    setState(() {
      _detailFuture = _loadDetail();
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
            title: 'Inicia sesión para ver este perfil',
            subtitle:
                'El detalle de la voz usa datos reales del backend y requiere sesión activa.',
            actionLabel: 'Volver al acceso',
            onAction: () => context.go('/login'),
          ),
        ],
      );
    }

    return FutureBuilder<_VoiceDetailData>(
      future: _detailFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.record_voice_over_outlined,
                title: 'Cargando perfil',
                subtitle:
                    'Estamos consultando la identidad vocal y sus muestras.',
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
                title: 'No pudimos abrir el perfil',
                subtitle:
                    'No fue posible consultar el detalle del perfil en este momento.',
                actionLabel: 'Reintentar',
                onAction: _refresh,
              ),
            ],
          );
        }

        final detail = snapshot.data!;
        final profile = detail.profile;
        final samples = detail.samples;

        return VFPageScaffold(
          children: [
            VFPanel(
              variant: VFPanelVariant.hero,
              gradient: AppGradients.hero,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              profile.name,
                              style: Theme.of(context)
                                  .textTheme
                                  .displaySmall
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: AppSpacing.sm),
                            Text(
                              profile.description?.trim().isNotEmpty == true
                                  ? profile.description!
                                  : readinessHint(
                                      score: profile.readinessScore,
                                      clipCount: profile.clipCount,
                                    ),
                              style: Theme.of(context).textTheme.bodyLarge,
                            ),
                          ],
                        ),
                      ),
                      VFStatusBadge.fromStatus(formatStatusLabel(profile.status)),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  Wrap(
                    spacing: AppSpacing.md,
                    runSpacing: AppSpacing.md,
                    children: [
                      _ProfileStat(
                        label: 'Identidad vocal',
                        value: '${profile.readinessScore.toInt()}%',
                      ),
                      _ProfileStat(
                        label: 'Muestras',
                        value: '${profile.clipCount}',
                      ),
                      _ProfileStat(
                        label: 'Duración total',
                        value: formatDurationSeconds(profile.totalDurationSeconds),
                      ),
                      _ProfileStat(
                        label: 'Limpieza',
                        value: describeNoise(profile.noiseScore),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            LayoutBuilder(
              builder: (context, constraints) {
                final compact = constraints.maxWidth < 980;

                final left = Column(
                  children: [
                    VFCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const VFSectionHeader(
                            title: 'Preparación del perfil',
                            subtitle:
                                'Mientras más muestras útiles tenga una voz, mejor suele mantenerse su identidad y su consistencia.',
                          ),
                          const SizedBox(height: AppSpacing.xl),
                          VFProgressBar(
                            value: profile.readinessScore / 100,
                            label: readinessHeadline(profile.readinessScore),
                            trailing: '${profile.readinessScore.toInt()}%',
                          ),
                          const SizedBox(height: AppSpacing.lg),
                          Text(
                            readinessHint(
                              score: profile.readinessScore,
                              clipCount: profile.clipCount,
                            ),
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                          const SizedBox(height: AppSpacing.xl),
                          const VFWaveformContainer(
                            title: 'Vista del perfil',
                            caption:
                                'Superficie lista para actividad, muestras y estado del perfil.',
                            height: 170,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    VFCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const VFSectionHeader(
                            title: 'Muestras recientes',
                            subtitle:
                                'Consulta el material ya asociado a esta voz y revisa si conviene sumar más cobertura.',
                          ),
                          const SizedBox(height: AppSpacing.xl),
                          if (samples.isEmpty)
                            const VFEmptyState(
                              icon: Icons.library_music_outlined,
                              title: 'Todavía no hay muestras',
                              subtitle:
                                  'Añade tus primeras tomas para empezar a construir esta identidad vocal.',
                            )
                          else
                            ...samples.take(4).map(
                                  (sample) => Padding(
                                    padding: const EdgeInsets.only(
                                      bottom: AppSpacing.md,
                                    ),
                                    child: _SampleListTile(sample: sample),
                                  ),
                                ),
                        ],
                      ),
                    ),
                  ],
                );

                final right = Column(
                  children: [
                    VFCard(
                      variant: VFCardVariant.elevated,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const VFSectionHeader(
                            title: 'Acciones',
                            subtitle:
                                'Mantén clara la siguiente acción y refuerza el perfil antes de crear una nueva conversión.',
                          ),
                          const SizedBox(height: AppSpacing.xl),
                          VFButton(
                            label: 'Añadir muestra',
                            expand: true,
                            size: VFButtonSize.lg,
                            leadingIcon: Icons.upload_file_outlined,
                            onPressed: () =>
                                context.go('/voices/${widget.voiceId}/upload'),
                          ),
                          const SizedBox(height: AppSpacing.md),
                          VFButton(
                            label: 'Crear conversión',
                            expand: true,
                            variant: VFButtonVariant.secondary,
                            leadingIcon: Icons.auto_awesome_motion_outlined,
                            onPressed: () => context.go('/conversions/create'),
                          ),
                          const SizedBox(height: AppSpacing.md),
                          VFButton(
                            label: 'Grabar muestra',
                            expand: true,
                            variant: VFButtonVariant.ghost,
                            trailingIcon: Icons.arrow_forward_rounded,
                            onPressed: () =>
                                context.go('/voices/${widget.voiceId}/record'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    VFPanel(
                      variant: VFPanelVariant.subdued,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          VFStatusBadge.fromStatus(
                            formatStatusLabel(profile.status),
                          ),
                          const SizedBox(height: AppSpacing.md),
                          Text(
                            readinessHint(
                              score: profile.readinessScore,
                              clipCount: profile.clipCount,
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
                      left,
                      const SizedBox(height: AppSpacing.md),
                      right,
                    ],
                  );
                }

                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(flex: 6, child: left),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(flex: 5, child: right),
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

class _VoiceLibraryCard extends StatelessWidget {
  const _VoiceLibraryCard({required this.profile});

  final VoiceProfile profile;

  @override
  Widget build(BuildContext context) {
    return VFCard(
      variant: VFCardVariant.interactive,
      onTap: () => context.go('/voices/${profile.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      profile.name,
                      style: Theme.of(context)
                          .textTheme
                          .headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Wrap(
                      spacing: AppSpacing.xs,
                      runSpacing: AppSpacing.xs,
                      children: [
                        VFChip(label: '${profile.clipCount} muestras'),
                        VFChip(
                          label: formatDurationSeconds(profile.totalDurationSeconds),
                        ),
                        VFChip(label: describeNoise(profile.noiseScore)),
                      ],
                    ),
                  ],
                ),
              ),
              VFStatusBadge.fromStatus(formatStatusLabel(profile.status)),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          VFProgressBar(
            value: profile.readinessScore / 100,
            label: readinessHeadline(profile.readinessScore),
            trailing: '${profile.readinessScore.toInt()}%',
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            readinessHint(
              score: profile.readinessScore,
              clipCount: profile.clipCount,
            ),
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: AppSpacing.xl),
          Wrap(
            spacing: AppSpacing.sm,
            runSpacing: AppSpacing.sm,
            children: [
              VFButton(
                label: 'Abrir perfil',
                onPressed: () => context.go('/voices/${profile.id}'),
              ),
              VFButton(
                label: 'Añadir muestra',
                variant: VFButtonVariant.secondary,
                onPressed: () => context.go('/voices/${profile.id}/upload'),
              ),
              VFButton(
                label: 'Crear conversión',
                variant: VFButtonVariant.ghost,
                trailingIcon: Icons.arrow_forward_rounded,
                onPressed: () => context.go('/conversions/create'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _LibraryMetric extends StatelessWidget {
  const _LibraryMetric({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 220,
      child: VFPanel(
        variant: VFPanelVariant.subdued,
        padding: const EdgeInsets.all(AppSpacing.lg),
        borderColor: AppColors.borderStrong,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: AppSpacing.sm),
            Text(
              value,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfileStat extends StatelessWidget {
  const _ProfileStat({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 170,
      child: VFPanel(
        variant: VFPanelVariant.subdued,
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: AppSpacing.sm),
            Text(
              value,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
    );
  }
}

class _SampleListTile extends StatelessWidget {
  const _SampleListTile({required this.sample});

  final VoiceSample sample;

  @override
  Widget build(BuildContext context) {
    return VFPanel(
      variant: VFPanelVariant.subdued,
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  sample.originalFilename,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
              ),
              VFStatusBadge.fromStatus(formatStatusLabel(sample.processingStatus)),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Wrap(
            spacing: AppSpacing.xs,
            runSpacing: AppSpacing.xs,
            children: [
              VFChip(label: formatSampleSource(sample.source)),
              VFChip(label: formatDurationSeconds(sample.durationSeconds)),
              VFChip(label: formatFileSize(sample.sizeBytes)),
            ],
          ),
        ],
      ),
    );
  }
}

class _CreateProfileDialog extends StatefulWidget {
  const _CreateProfileDialog({required this.repository});

  final VoiceRepository repository;

  @override
  State<_CreateProfileDialog> createState() => _CreateProfileDialogState();
}

class _CreateProfileDialogState extends State<_CreateProfileDialog> {
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _isSaving = false;
  String? _errorMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    final description = _descriptionController.text.trim();
    if (name.length < 2) {
      setState(() => _errorMessage = 'Asigna un nombre más claro al perfil.');
      return;
    }
    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });
    try {
      final profile = await widget.repository.createProfile(
        name: name,
        description: description,
      );
      if (!mounted) {
        return;
      }
      Navigator.of(context).pop(profile);
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _errorMessage = error.toString());
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: VFCard(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const VFSectionHeader(
              title: 'Crear perfil de voz',
              subtitle:
                  'Este perfil quedará listo para recibir muestras y usarse en nuevas conversiones.',
            ),
            const SizedBox(height: AppSpacing.xl),
            VFInput(
              label: 'Nombre del perfil',
              hintText: 'Narrador principal',
              prefixIcon: Icons.record_voice_over_outlined,
              controller: _nameController,
            ),
            const SizedBox(height: AppSpacing.md),
            VFInput(
              label: 'Descripción',
              hintText: 'Uso previsto, estilo o notas de la voz',
              prefixIcon: Icons.notes_outlined,
              maxLines: 3,
              controller: _descriptionController,
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(
                _errorMessage!,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.danger500,
                    ),
              ),
            ],
            const SizedBox(height: AppSpacing.xl),
            Wrap(
              spacing: AppSpacing.md,
              runSpacing: AppSpacing.md,
              children: [
                VFButton(
                  label: 'Crear perfil',
                  leadingIcon: Icons.add_circle_outline,
                  onPressed: _submit,
                  isLoading: _isSaving,
                ),
                VFButton(
                  label: 'Cancelar',
                  variant: VFButtonVariant.secondary,
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _VoiceDetailData {
  const _VoiceDetailData({
    required this.profile,
    required this.samples,
  });

  final VoiceProfile profile;
  final List<VoiceSample> samples;
}

class UploadSamplesScreen extends StatefulWidget {
  const UploadSamplesScreen({super.key, required this.voiceId});

  final String voiceId;

  @override
  State<UploadSamplesScreen> createState() => _UploadSamplesScreenState();
}

class _UploadSamplesScreenState extends State<UploadSamplesScreen> {
  final _picker = AudioFilePicker();
  bool _isUploading = false;
  late Future<_VoiceDetailData> _detailFuture;

  @override
  void initState() {
    super.initState();
    _detailFuture = _loadDetail();
  }

  VoiceRepository get _repository => VoiceForgeScope.read(context).voiceRepository;

  Future<_VoiceDetailData> _loadDetail() async {
    final profile = await _repository.getProfile(widget.voiceId);
    final samples = await _repository.listSamples(widget.voiceId);
    samples.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return _VoiceDetailData(profile: profile, samples: samples);
  }

  Future<void> _refresh() async {
    setState(() {
      _detailFuture = _loadDetail();
    });
  }

  Future<void> _pickAndUpload({required String source}) async {
    final selected = await _picker.pickSingleAudio();
    if (selected == null) {
      return;
    }
    setState(() => _isUploading = true);
    try {
      await _repository.uploadSample(
        profileId: widget.voiceId,
        file: selected,
        source: source,
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('La muestra se subió correctamente.')),
      );
      await _refresh();
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) {
        setState(() => _isUploading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_VoiceDetailData>(
      future: _detailFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.cloud_upload_outlined,
                title: 'Cargando espacio de muestras',
                subtitle:
                    'Estamos preparando el perfil y sus clips actuales.',
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
                title: 'No pudimos cargar las muestras',
                subtitle:
                    'No fue posible consultar el perfil o sus archivos en este momento.',
                actionLabel: 'Reintentar',
                onAction: _refresh,
              ),
            ],
          );
        }

        final detail = snapshot.data!;
        final profile = detail.profile;
        final samples = detail.samples;

        return VFPageScaffold(
          children: [
            VFPanel(
              variant: VFPanelVariant.hero,
              gradient: AppGradients.hero,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  VFSectionHeader(
                    eyebrow: 'Añadir muestra',
                    title: 'Refuerza ${profile.name} con nuevo material',
                    subtitle:
                        'Sube clips claros, variados y bien capturados para seguir mejorando la identidad vocal del perfil.',
                    trailing: const VFChip(
                      label: 'Recomendado',
                      tone: VFChipTone.recommended,
                      icon: Icons.stars_outlined,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.xl),
                  Wrap(
                    spacing: AppSpacing.sm,
                    runSpacing: AppSpacing.sm,
                    children: [
                      VFChip(label: '${profile.clipCount} muestras'),
                      VFChip(
                        label: formatDurationSeconds(profile.totalDurationSeconds),
                      ),
                      VFChip(label: describeNoise(profile.noiseScore)),
                    ],
                  ),
                ],
              ),
            ),
            LayoutBuilder(
              builder: (context, constraints) {
                final compact = constraints.maxWidth < 980;

                final uploader = VFCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const VFSectionHeader(
                        title: 'Carga de archivos',
                        subtitle:
                            'La superficie queda lista para seleccionar y subir nuevas muestras directamente al backend.',
                      ),
                      const SizedBox(height: AppSpacing.xl),
                      VFPanel(
                        variant: VFPanelVariant.subdued,
                        borderColor: AppColors.primary400,
                        child: Column(
                          children: [
                            Icon(
                              Icons.cloud_upload_outlined,
                              size: 42,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                            const SizedBox(height: AppSpacing.md),
                            Text(
                              'Selecciona un archivo de audio desde tu dispositivo',
                              textAlign: TextAlign.center,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: AppSpacing.xs),
                            Text(
                              'Prioriza clips claros, con buena dicción y sin ruido dominante.',
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                            const SizedBox(height: AppSpacing.xl),
                            VFButton(
                              label: 'Seleccionar y subir',
                              leadingIcon: Icons.folder_open_outlined,
                              onPressed: () => _pickAndUpload(source: 'upload'),
                              isLoading: _isUploading,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );

                final list = VFCard(
                  variant: VFCardVariant.elevated,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const VFSectionHeader(
                        title: 'Muestras actuales',
                        subtitle:
                            'Revisa qué material ya tiene el perfil antes de seguir ampliando su cobertura.',
                      ),
                      const SizedBox(height: AppSpacing.xl),
                      if (samples.isEmpty)
                        const VFEmptyState(
                          icon: Icons.library_music_outlined,
                          title: 'Aún no hay muestras',
                          subtitle:
                              'Tu primera subida aparecerá aquí con su duración, tamaño y estado.',
                        )
                      else
                        ...samples.map(
                          (sample) => Padding(
                            padding:
                                const EdgeInsets.only(bottom: AppSpacing.md),
                            child: _SampleListTile(sample: sample),
                          ),
                        ),
                    ],
                  ),
                );

                if (compact) {
                  return Column(
                    children: [
                      uploader,
                      const SizedBox(height: AppSpacing.md),
                      list,
                    ],
                  );
                }

                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(flex: 7, child: uploader),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(flex: 5, child: list),
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

class RecordSampleScreen extends StatefulWidget {
  const RecordSampleScreen({super.key, required this.voiceId});

  final String voiceId;

  @override
  State<RecordSampleScreen> createState() => _RecordSampleScreenState();
}

enum _RecordingPhase { idle, recording, preview }

class _RecordSampleScreenState extends State<RecordSampleScreen> {
  final _recorder = record.AudioRecorder();
  final _player = just_audio.AudioPlayer();
  _RecordingPhase _phase = _RecordingPhase.idle;
  bool _hasPermission = false;
  bool _permissionDenied = false;
  bool _isUploading = false;
  Timer? _timer;
  int _elapsedSeconds = 0;
  String? _recordedPath;
  Uint8List? _recordedBytes;

  @override
  void initState() {
    super.initState();
    _checkPermission();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _recorder.dispose();
    _player.dispose();
    _cleanupTempFile();
    super.dispose();
  }

  Future<void> _checkPermission() async {
    final granted = await _recorder.hasPermission();
    if (mounted) {
      setState(() {
        _hasPermission = granted;
        _permissionDenied = !granted;
      });
    }
  }

  Future<void> _requestPermission() async {
    final status = await permission_handler.Permission.microphone.request();
    if (mounted) {
      setState(() {
        _hasPermission = status.isGranted;
        _permissionDenied = status.isPermanentlyDenied || status.isDenied;
      });
    }
  }

  Future<void> _startRecording() async {
    if (!_hasPermission) {
      await _requestPermission();
      if (!_hasPermission) return;
    }

    _cleanupTempFile();

    final tempDir = await _getTempDirectory();
    final path = '$tempDir/vf_recording_${DateTime.now().millisecondsSinceEpoch}.wav';

    await _recorder.start(
      const record.RecordConfig(
        encoder: record.AudioEncoder.wav,
        sampleRate: 44100,
        numChannels: 1,
      ),
      path: path,
    );

    setState(() {
      _phase = _RecordingPhase.recording;
      _elapsedSeconds = 0;
      _recordedPath = path;
      _recordedBytes = null;
    });

    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsedSeconds++);
    });
  }

  Future<void> _stopRecording() async {
    _timer?.cancel();
    final path = await _recorder.stop();
    if (path == null || !mounted) return;

    final file = io.File(path);
    final bytes = await file.readAsBytes();

    setState(() {
      _phase = _RecordingPhase.preview;
      _recordedPath = path;
      _recordedBytes = bytes;
    });
  }

  Future<void> _playPreview() async {
    final path = _recordedPath;
    if (path == null) return;
    await _player.setFilePath(path);
    await _player.play();
  }

  Future<void> _stopPreview() async {
    await _player.stop();
  }

  Future<void> _discardAndRestart() async {
    await _player.stop();
    _cleanupTempFile();
    setState(() {
      _phase = _RecordingPhase.idle;
      _elapsedSeconds = 0;
      _recordedPath = null;
      _recordedBytes = null;
    });
  }

  Future<void> _uploadRecording() async {
    final bytes = _recordedBytes;
    if (bytes == null) return;

    setState(() => _isUploading = true);
    try {
      final scope = VoiceForgeScope.read(context);
      final uploadFile = AudioUploadFile(
        name: 'recording_${DateTime.now().millisecondsSinceEpoch}.wav',
        bytes: bytes,
        sizeBytes: bytes.length,
        mimeType: 'audio/wav',
      );
      await scope.voiceRepository.uploadSample(
        profileId: widget.voiceId,
        file: uploadFile,
        source: 'microphone',
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Grabación subida correctamente.')),
      );
      _cleanupTempFile();
      context.go('/voices/${widget.voiceId}');
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al subir: $error')),
      );
    } finally {
      if (mounted) setState(() => _isUploading = false);
    }
  }

  void _cleanupTempFile() {
    final path = _recordedPath;
    if (path != null) {
      final file = io.File(path);
      if (file.existsSync()) {
        try {
          file.deleteSync();
        } on io.FileSystemException {
          // Best-effort cleanup; file may be locked by player
        }
      }
    }
  }

  Future<String> _getTempDirectory() async {
    return io.Directory.systemTemp.path;
  }

  String _formatElapsed(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_permissionDenied && !_hasPermission) {
      return VFPageScaffold(
        children: [
          VFStatePanel(
            icon: Icons.mic_off_outlined,
            title: 'Permiso de micrófono denegado',
            subtitle:
                'VoiceForge necesita acceso al micrófono para grabar muestras de voz. '
                'Puedes activar el permiso desde la configuración de tu dispositivo.',
            actionLabel: 'Abrir configuración',
            onAction: () => permission_handler.openAppSettings(),
          ),
          VFButton(
            label: 'Reintentar permiso',
            variant: VFButtonVariant.secondary,
            expand: true,
            onPressed: _requestPermission,
          ),
          VFButton(
            label: 'Ir a subir archivo',
            variant: VFButtonVariant.ghost,
            expand: true,
            leadingIcon: Icons.upload_file_outlined,
            onPressed: () => context.go('/voices/${widget.voiceId}/upload'),
          ),
        ],
      );
    }

    return VFPageScaffold(
      children: [
        const VFSectionHeader(
          eyebrow: 'Grabar muestra',
          title: 'Captura directa por micrófono',
          subtitle:
              'Graba un clip de voz claro y sin ruido. Prioriza buena dicción y variedad tonal.',
        ),

        // Recording controls
        VFCard(
          child: Column(
            children: [
              // Timer display
              Semantics(
                label: 'Tiempo de grabación: ${_formatElapsed(_elapsedSeconds)}',
                child: Text(
                  _formatElapsed(_elapsedSeconds),
                  style: theme.textTheme.displayMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    fontFeatures: const [FontFeature.tabularFigures()],
                    color: _phase == _RecordingPhase.recording
                        ? AppColors.danger500
                        : AppColors.text100,
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(
                switch (_phase) {
                  _RecordingPhase.idle => 'Listo para grabar',
                  _RecordingPhase.recording => 'Grabando...',
                  _RecordingPhase.preview => 'Grabación lista',
                },
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: AppColors.text300,
                ),
              ),
              const SizedBox(height: AppSpacing.xxl),

              // Main action button
              if (_phase == _RecordingPhase.idle)
                Semantics(
                  button: true,
                  label: 'Iniciar grabación',
                  child: VFButton(
                    label: 'Grabar',
                    size: VFButtonSize.lg,
                    leadingIcon: Icons.mic_outlined,
                    onPressed: _startRecording,
                  ),
                ),
              if (_phase == _RecordingPhase.recording)
                Semantics(
                  button: true,
                  label: 'Detener grabación',
                  child: VFButton(
                    label: 'Detener',
                    size: VFButtonSize.lg,
                    variant: VFButtonVariant.destructive,
                    leadingIcon: Icons.stop_rounded,
                    onPressed: _stopRecording,
                  ),
                ),
              if (_phase == _RecordingPhase.preview) ...[
                // Preview controls
                Wrap(
                  spacing: AppSpacing.md,
                  runSpacing: AppSpacing.md,
                  alignment: WrapAlignment.center,
                  children: [
                    Semantics(
                      button: true,
                      label: 'Reproducir grabación',
                      child: VFButton(
                        label: 'Reproducir',
                        variant: VFButtonVariant.secondary,
                        leadingIcon: Icons.play_arrow_rounded,
                        onPressed: _playPreview,
                      ),
                    ),
                    Semantics(
                      button: true,
                      label: 'Detener reproducción',
                      child: VFButton(
                        label: 'Detener',
                        variant: VFButtonVariant.secondary,
                        leadingIcon: Icons.stop_rounded,
                        onPressed: _stopPreview,
                      ),
                    ),
                    Semantics(
                      button: true,
                      label: 'Grabar de nuevo',
                      child: VFButton(
                        label: 'Repetir',
                        variant: VFButtonVariant.ghost,
                        leadingIcon: Icons.refresh_rounded,
                        onPressed: _discardAndRestart,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.xl),
                if (_recordedBytes != null)
                  VFPanel(
                    variant: VFPanelVariant.subdued,
                    child: Row(
                      children: [
                        const Icon(Icons.audio_file_outlined, color: AppColors.accentCyan),
                        const SizedBox(width: AppSpacing.md),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Grabación de ${_formatElapsed(_elapsedSeconds)}',
                                style: theme.textTheme.bodyMedium
                                    ?.copyWith(fontWeight: FontWeight.w600),
                              ),
                              Text(
                                formatFileSize(_recordedBytes!.length),
                                style: theme.textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: AppSpacing.lg),
                Semantics(
                  button: true,
                  label: 'Guardar y subir grabación',
                  child: VFButton(
                    label: 'Guardar y subir',
                    size: VFButtonSize.lg,
                    expand: true,
                    leadingIcon: Icons.cloud_upload_outlined,
                    isLoading: _isUploading,
                    onPressed: _isUploading ? null : _uploadRecording,
                  ),
                ),
              ],
            ],
          ),
        ),

        // Navigation fallback
        Wrap(
          spacing: AppSpacing.md,
          runSpacing: AppSpacing.md,
          children: [
            VFButton(
              label: 'Subir archivo',
              variant: VFButtonVariant.secondary,
              leadingIcon: Icons.upload_file_outlined,
              onPressed: () => context.go('/voices/${widget.voiceId}/upload'),
            ),
            VFButton(
              label: 'Volver al perfil',
              variant: VFButtonVariant.ghost,
              onPressed: () => context.go('/voices/${widget.voiceId}'),
            ),
          ],
        ),
      ],
    );
  }
}
