import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:just_audio/just_audio.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_spacing.dart';
import '../../core/files/audio_file_picker.dart';
import '../../core/files/audio_upload_file.dart';
import '../../core/files/download_service.dart';
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

// ---------------------------------------------------------------------------
// CreateConversionScreen
// ---------------------------------------------------------------------------

class CreateConversionScreen extends StatefulWidget {
  const CreateConversionScreen({super.key});

  @override
  State<CreateConversionScreen> createState() => _CreateConversionScreenState();
}

class _CreateConversionScreenState extends State<CreateConversionScreen> {
  late Future<List<VoiceProfile>> _profilesFuture;
  VoiceProfile? _selectedProfile;
  String _mode = 'studio';
  AudioUploadFile? _sourceFile;
  bool _isBusy = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _profilesFuture = VoiceForgeScope.read(context).voiceRepository.listProfiles();
  }

  Future<void> _pickFile() async {
    final file = await AudioFilePicker().pickSingleAudio();
    if (file != null) {
      setState(() => _sourceFile = file);
    }
  }

  Future<void> _submit() async {
    if (_selectedProfile == null || _sourceFile == null) return;

    setState(() {
      _isBusy = true;
      _errorMessage = null;
    });

    try {
      final scope = VoiceForgeScope.read(context);
      final job = await scope.conversionRepository.createJob(
        voiceProfileId: _selectedProfile!.id,
        mode: _mode,
        file: _sourceFile!,
      );
      if (mounted) {
        context.go('/conversions/history/${job.id}');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _errorMessage = e.toString());
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al crear conversión: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return FutureBuilder<List<VoiceProfile>>(
      future: _profilesFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.auto_awesome_motion_outlined,
                title: 'Preparando conversión',
                subtitle: 'Cargando perfiles de voz disponibles.',
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
                title: 'No se pudieron cargar los perfiles',
                subtitle: 'Revisa la conexión e inténtalo de nuevo.',
                actionLabel: 'Reintentar',
                onAction: () {
                  setState(() {
                    _profilesFuture =
                        VoiceForgeScope.read(context).voiceRepository.listProfiles();
                  });
                },
              ),
            ],
          );
        }

        final profiles = snapshot.data!;

        if (profiles.isEmpty) {
          return VFPageScaffold(
            children: [
              VFEmptyState(
                icon: Icons.library_music_outlined,
                title: 'Necesitas al menos un perfil de voz',
                subtitle:
                    'Ve a la biblioteca y crea un perfil con muestras antes de iniciar una conversión.',
                actionLabel: 'Ir a voces',
                onAction: () => context.go('/voices'),
              ),
            ],
          );
        }

        final canSubmit =
            _selectedProfile != null && _sourceFile != null && !_isBusy;

        return VFPageScaffold(
          children: [
            const VFSectionHeader(
              title: 'Nueva conversión',
              subtitle:
                  'Elige una voz de referencia, sube el audio a transformar y lanza el proceso.',
            ),

            // --- Profile selector ---
            VFCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Perfil de voz',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    'El audio resultante adoptará la identidad vocal de este perfil.',
                    style: theme.textTheme.bodySmall,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  DropdownButtonFormField<String>(
                    initialValue: _selectedProfile?.id,
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: AppColors.bg900,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: AppColors.borderSoft),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: AppColors.borderSoft),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: AppSpacing.lg,
                        vertical: AppSpacing.md,
                      ),
                    ),
                    dropdownColor: AppColors.surface700,
                    hint: Text(
                      'Selecciona un perfil',
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: AppColors.text300),
                    ),
                    items: profiles.map((p) {
                      return DropdownMenuItem(
                        value: p.id,
                        child: Text(
                          '${p.name}  (${p.readinessScore.toInt()}%)',
                          style: theme.textTheme.bodyMedium,
                        ),
                      );
                    }).toList(),
                    onChanged: (id) {
                      setState(() {
                        _selectedProfile =
                            profiles.firstWhere((p) => p.id == id);
                      });
                    },
                  ),
                  if (_selectedProfile != null) ...[
                    const SizedBox(height: AppSpacing.lg),
                    VFProgressBar(
                      value: _selectedProfile!.readinessScore / 100,
                      label: readinessHeadline(_selectedProfile!.readinessScore),
                      trailing: '${_selectedProfile!.readinessScore.toInt()}%',
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      '${_selectedProfile!.clipCount} muestras  •  ${formatDurationSeconds(_selectedProfile!.totalDurationSeconds)}',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ],
              ),
            ),

            // --- Mode selector ---
            VFCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Modo de conversión',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Row(
                    children: [
                      Expanded(
                        child: _ModeOption(
                          label: 'Alta calidad',
                          description: 'Procesamiento offline con máxima fidelidad.',
                          icon: Icons.high_quality_outlined,
                          selected: _mode == 'studio',
                          onTap: () => setState(() => _mode = 'studio'),
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: _ModeOption(
                          label: 'Rápido',
                          description: 'Menor latencia, calidad experimental.',
                          icon: Icons.bolt_outlined,
                          selected: _mode == 'live',
                          onTap: () => setState(() => _mode = 'live'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // --- Source audio ---
            VFCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Audio fuente',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    'El contenido hablado de este audio se conservará, pero con la voz del perfil seleccionado.',
                    style: theme.textTheme.bodySmall,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  if (_sourceFile != null) ...[
                    VFPanel(
                      variant: VFPanelVariant.subdued,
                      child: Row(
                        children: [
                          const Icon(
                            Icons.audio_file_outlined,
                            color: AppColors.accentCyan,
                          ),
                          const SizedBox(width: AppSpacing.md),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _sourceFile!.name,
                                  style: theme.textTheme.bodyMedium
                                      ?.copyWith(fontWeight: FontWeight.w600),
                                  overflow: TextOverflow.ellipsis,
                                ),
                                Text(
                                  formatFileSize(_sourceFile!.sizeBytes),
                                  style: theme.textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close, size: 18),
                            onPressed: () =>
                                setState(() => _sourceFile = null),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                  ],
                  VFButton(
                    label: _sourceFile == null
                        ? 'Seleccionar archivo de audio'
                        : 'Cambiar archivo',
                    variant: VFButtonVariant.secondary,
                    leadingIcon: Icons.upload_file_outlined,
                    expand: true,
                    onPressed: _pickFile,
                  ),
                ],
              ),
            ),

            // --- Error ---
            if (_errorMessage != null)
              VFPanel(
                variant: VFPanelVariant.subdued,
                borderColor: AppColors.danger500.withValues(alpha: 0.5),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: AppColors.danger500),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: theme.textTheme.bodySmall
                            ?.copyWith(color: AppColors.danger500),
                      ),
                    ),
                  ],
                ),
              ),

            // --- Submit ---
            VFButton(
              label: 'Crear conversión',
              size: VFButtonSize.lg,
              expand: true,
              leadingIcon: Icons.auto_awesome_motion_outlined,
              isLoading: _isBusy,
              onPressed: canSubmit ? _submit : null,
            ),
          ],
        );
      },
    );
  }
}

class _ModeOption extends StatelessWidget {
  const _ModeOption({
    required this.label,
    required this.description,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final String description;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return VFCard(
      variant: VFCardVariant.interactive,
      onTap: onTap,
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                icon,
                color: selected ? AppColors.primary400 : AppColors.text300,
              ),
              const Spacer(),
              if (selected)
                const VFChip(label: 'Activo', tone: VFChipTone.recommended),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            label,
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w700,
              color: selected ? AppColors.text100 : AppColors.text300,
            ),
          ),
          const SizedBox(height: AppSpacing.xxs),
          Text(description, style: theme.textTheme.bodySmall),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// ConversionHistoryScreen
// ---------------------------------------------------------------------------

class ConversionHistoryScreen extends StatefulWidget {
  const ConversionHistoryScreen({super.key});

  @override
  State<ConversionHistoryScreen> createState() =>
      _ConversionHistoryScreenState();
}

class _ConversionHistoryScreenState extends State<ConversionHistoryScreen> {
  late Future<List<ConversionJob>> _jobsFuture;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    _jobsFuture = _loadJobs();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<List<ConversionJob>> _loadJobs() async {
    final jobs =
        await VoiceForgeScope.read(context).conversionRepository.listJobs();
    jobs.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    _schedulePollIfNeeded(jobs);
    return jobs;
  }

  void _schedulePollIfNeeded(List<ConversionJob> jobs) {
    _pollTimer?.cancel();
    final hasPending = jobs.any((j) => _isInProgress(j.status));
    if (hasPending) {
      _pollTimer = Timer(const Duration(seconds: 5), () {
        if (mounted) _refresh();
      });
    }
  }

  static bool _isInProgress(String status) {
    return status == 'pending' ||
        status == 'queued' ||
        status == 'processing' ||
        status == 'running';
  }

  void _refresh() {
    setState(() {
      _jobsFuture = _loadJobs();
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<ConversionJob>>(
      future: _jobsFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.history_outlined,
                title: 'Cargando historial',
                subtitle: 'Consultando tus conversiones recientes.',
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
                title: 'Error al cargar el historial',
                subtitle: 'Revisa la conexión e inténtalo de nuevo.',
                actionLabel: 'Reintentar',
                onAction: _refresh,
              ),
            ],
          );
        }

        final jobs = snapshot.data!;

        if (jobs.isEmpty) {
          return VFPageScaffold(
            children: [
              VFEmptyState(
                icon: Icons.history_outlined,
                title: 'Sin conversiones todavía',
                subtitle:
                    'Cuando crees tu primera conversión, aparecerá aquí con su estado y resultados.',
                actionLabel: 'Crear conversión',
                onAction: () => context.go('/conversions/create'),
              ),
            ],
          );
        }

        return VFPageScaffold(
          children: [
            VFSectionHeader(
              title: 'Historial de conversiones',
              subtitle: '${jobs.length} conversiones registradas.',
              trailing: VFButton(
                label: 'Nueva',
                size: VFButtonSize.sm,
                leadingIcon: Icons.add,
                onPressed: () => context.go('/conversions/create'),
              ),
            ),
            ...jobs.map((job) => _JobTile(job: job)),
          ],
        );
      },
    );
  }
}

class _JobTile extends StatelessWidget {
  const _JobTile({required this.job});

  final ConversionJob job;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return VFCard(
      variant: VFCardVariant.interactive,
      onTap: () => context.go('/conversions/history/${job.id}'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  job.sourceAudioFilename,
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              VFStatusBadge.fromStatus(formatStatusLabel(job.status)),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          Wrap(
            spacing: AppSpacing.md,
            runSpacing: AppSpacing.xs,
            children: [
              Text(
                formatModeLabel(job.mode),
                style: theme.textTheme.bodySmall,
              ),
              Text(
                formatDurationSeconds(job.sourceAudioDurationSeconds),
                style: theme.textTheme.bodySmall,
              ),
              Text(
                formatRelativeDate(job.createdAt),
                style: theme.textTheme.bodySmall
                    ?.copyWith(color: AppColors.text300),
              ),
            ],
          ),
          if (job.processingDurationMs != null) ...[
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Procesado en ${formatDurationSeconds(job.processingDurationMs! / 1000)}',
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: AppColors.text300),
            ),
          ],
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// ResultPlayerScreen
// ---------------------------------------------------------------------------

class ResultPlayerScreen extends StatefulWidget {
  const ResultPlayerScreen({super.key, required this.jobId});

  final String jobId;

  @override
  State<ResultPlayerScreen> createState() => _ResultPlayerScreenState();
}

class _ResultPlayerScreenState extends State<ResultPlayerScreen> {
  late Future<ConversionJob> _jobFuture;
  List<ConvertedAudio>? _outputs;
  Timer? _pollTimer;

  // Audio playback
  final AudioPlayer _audioPlayer = AudioPlayer();
  String? _playingOutputId;
  bool _isPlaying = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;

  @override
  void initState() {
    super.initState();
    _jobFuture = _loadJob();
    _audioPlayer.positionStream.listen((pos) {
      if (mounted) setState(() => _position = pos);
    });
    _audioPlayer.durationStream.listen((dur) {
      if (mounted && dur != null) setState(() => _duration = dur);
    });
    _audioPlayer.playerStateStream.listen((state) {
      if (mounted) {
        setState(() => _isPlaying = state.playing);
        if (state.processingState == ProcessingState.completed) {
          _audioPlayer.seek(Duration.zero);
          _audioPlayer.pause();
        }
      }
    });
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<ConversionJob> _loadJob() async {
    final scope = VoiceForgeScope.read(context);
    final job = await scope.conversionRepository.getJob(widget.jobId);

    if (job.status == 'completed') {
      final outputs = await scope.conversionRepository.getOutputs(widget.jobId);
      if (mounted) setState(() => _outputs = outputs);
    } else if (_isInProgressStatus(job.status)) {
      _schedulePoll();
    }

    return job;
  }

  void _schedulePoll() {
    _pollTimer?.cancel();
    _pollTimer = Timer(const Duration(seconds: 3), () {
      if (mounted) {
        setState(() {
          _jobFuture = _loadJob();
        });
      }
    });
  }

  static bool _isInProgressStatus(String status) {
    return status == 'pending' ||
        status == 'queued' ||
        status == 'processing' ||
        status == 'running';
  }

  Future<void> _playOutput(ConvertedAudio output) async {
    final scope = VoiceForgeScope.read(context);
    try {
      final bytes = await scope.conversionRepository.downloadOutput(
        jobId: widget.jobId,
        outputId: output.id,
      );

      // Use data URI — works on both web and native with just_audio
      final mimeType = output.format == 'wav' ? 'audio/wav' : 'audio/${output.format}';
      final b64 = base64Encode(bytes);
      final dataUri = 'data:$mimeType;base64,$b64';
      await _audioPlayer.setUrl(dataUri);

      setState(() => _playingOutputId = output.id);
      await _audioPlayer.play();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al reproducir: $e')),
        );
      }
    }
  }

  Future<void> _downloadOutput(ConvertedAudio output) async {
    final scope = VoiceForgeScope.read(context);
    try {
      final bytes = await scope.conversionRepository.downloadOutput(
        jobId: widget.jobId,
        outputId: output.id,
      );
      final downloadService = createDownloadService();
      final result = await downloadService.saveBytes(
        filename: 'voiceforge_${output.id}.${output.format}',
        bytes: bytes,
        contentType: output.format == 'wav' ? 'audio/wav' : 'audio/${output.format}',
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result.message)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al descargar: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return FutureBuilder<ConversionJob>(
      future: _jobFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const VFPageScaffold(
            children: [
              VFStatePanel(
                icon: Icons.auto_awesome_motion_outlined,
                title: 'Cargando resultado',
                subtitle: 'Obteniendo detalles de la conversión.',
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
                title: 'Error al cargar el resultado',
                subtitle: 'No se pudo obtener la información del trabajo.',
                actionLabel: 'Reintentar',
                onAction: () {
                  setState(() => _jobFuture = _loadJob());
                },
              ),
            ],
          );
        }

        final job = snapshot.data!;

        return VFPageScaffold(
          children: [
            // --- Header ---
            VFSectionHeader(
              title: job.sourceAudioFilename,
              subtitle: 'Conversión ${formatModeLabel(job.mode).toLowerCase()}',
              trailing: VFStatusBadge.fromStatus(formatStatusLabel(job.status)),
            ),

            // --- Metadata ---
            VFCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Detalles',
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  _MetadataRow(
                    label: 'Backend',
                    value: job.backend.toUpperCase().replaceAll('_', ' '),
                  ),
                  _MetadataRow(
                    label: 'Modo',
                    value: formatModeLabel(job.mode),
                  ),
                  _MetadataRow(
                    label: 'Duración fuente',
                    value: formatDurationSeconds(job.sourceAudioDurationSeconds),
                  ),
                  if (job.processingDurationMs != null)
                    _MetadataRow(
                      label: 'Tiempo de procesamiento',
                      value: formatDurationSeconds(
                        job.processingDurationMs! / 1000,
                      ),
                    ),
                  _MetadataRow(
                    label: 'Creado',
                    value: formatRelativeDate(job.createdAt),
                  ),
                ],
              ),
            ),

            // --- In-progress state ---
            if (_isInProgressStatus(job.status))
              VFPanel(
                variant: VFPanelVariant.subdued,
                child: Column(
                  children: [
                    SizedBox(
                      width: 28,
                      height: 28,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.4,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    Text(
                      'Conversión en progreso',
                      style: theme.textTheme.titleLarge
                          ?.copyWith(fontWeight: FontWeight.w700),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      'El audio se está procesando. Esta página se actualiza automáticamente.',
                      style: theme.textTheme.bodyMedium,
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),

            // --- Failed state ---
            if (job.status == 'failed')
              VFPanel(
                variant: VFPanelVariant.subdued,
                borderColor: AppColors.danger500.withValues(alpha: 0.5),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.error_outline,
                          color: AppColors.danger500,
                        ),
                        const SizedBox(width: AppSpacing.md),
                        Text(
                          'La conversión falló',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                            color: AppColors.danger500,
                          ),
                        ),
                      ],
                    ),
                    if (job.errorCategory != null) ...[
                      const SizedBox(height: AppSpacing.md),
                      _MetadataRow(
                        label: 'Categoría',
                        value: job.errorCategory!,
                      ),
                    ],
                    if (job.errorMessage != null) ...[
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        job.errorMessage!,
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                    const SizedBox(height: AppSpacing.lg),
                    VFButton(
                      label: 'Volver al historial',
                      variant: VFButtonVariant.secondary,
                      onPressed: () => context.go('/conversions/history'),
                    ),
                  ],
                ),
              ),

            // --- Completed: outputs ---
            if (job.status == 'completed' && _outputs != null) ...[
              VFSectionHeader(
                title: 'Resultados',
                subtitle: '${_outputs!.length} archivo(s) generado(s).',
              ),
              ..._outputs!.map((output) => _OutputCard(
                    output: output,
                    isPlaying:
                        _playingOutputId == output.id && _isPlaying,
                    position: _playingOutputId == output.id
                        ? _position
                        : Duration.zero,
                    duration: _playingOutputId == output.id
                        ? _duration
                        : Duration.zero,
                    onPlay: () => _playOutput(output),
                    onPause: () => _audioPlayer.pause(),
                    onSeek: (value) =>
                        _audioPlayer.seek(Duration(milliseconds: value)),
                    onDownload: () => _downloadOutput(output),
                  )),
            ],

            // --- Navigation ---
            if (job.status == 'completed' || job.status == 'failed')
              Row(
                children: [
                  Expanded(
                    child: VFButton(
                      label: 'Nueva conversión',
                      leadingIcon: Icons.add,
                      onPressed: () => context.go('/conversions/create'),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: VFButton(
                      label: 'Ver historial',
                      variant: VFButtonVariant.secondary,
                      trailingIcon: Icons.arrow_forward_rounded,
                      onPressed: () => context.go('/conversions/history'),
                    ),
                  ),
                ],
              ),
          ],
        );
      },
    );
  }
}

class _MetadataRow extends StatelessWidget {
  const _MetadataRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        children: [
          SizedBox(
            width: 180,
            child: Text(
              label,
              style:
                  theme.textTheme.bodySmall?.copyWith(color: AppColors.text300),
            ),
          ),
          Expanded(
            child: Text(value, style: theme.textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }
}

class _OutputCard extends StatelessWidget {
  const _OutputCard({
    required this.output,
    required this.isPlaying,
    required this.position,
    required this.duration,
    required this.onPlay,
    required this.onPause,
    required this.onSeek,
    required this.onDownload,
  });

  final ConvertedAudio output;
  final bool isPlaying;
  final Duration position;
  final Duration duration;
  final VoidCallback onPlay;
  final VoidCallback onPause;
  final ValueChanged<int> onSeek;
  final VoidCallback onDownload;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasAudio = duration.inMilliseconds > 0;

    return VFCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.audio_file_outlined, color: AppColors.accentCyan),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Audio convertido (.${output.format})',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    Text(
                      '${formatDurationSeconds(output.durationSeconds)}  •  ${formatFileSize(output.sizeBytes)}  •  ${output.sampleRate} Hz',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),

          // --- Playback controls ---
          VFPanel(
            variant: VFPanelVariant.subdued,
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              children: [
                Row(
                  children: [
                    IconButton(
                      icon: Icon(
                        isPlaying
                            ? Icons.pause_circle_filled
                            : Icons.play_circle_filled,
                        size: 40,
                        color: AppColors.primary400,
                      ),
                      onPressed: isPlaying ? onPause : onPlay,
                    ),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        children: [
                          SliderTheme(
                            data: SliderThemeData(
                              trackHeight: 4,
                              thumbShape: const RoundSliderThumbShape(
                                enabledThumbRadius: 6,
                              ),
                              activeTrackColor: AppColors.primary400,
                              inactiveTrackColor: AppColors.surface700,
                              thumbColor: AppColors.primary400,
                              overlayColor:
                                  AppColors.primary400.withValues(alpha: 0.12),
                            ),
                            child: Slider(
                              value: hasAudio
                                  ? position.inMilliseconds
                                      .clamp(0, duration.inMilliseconds)
                                      .toDouble()
                                  : 0,
                              max: hasAudio
                                  ? duration.inMilliseconds.toDouble()
                                  : 1,
                              onChanged: hasAudio
                                  ? (v) => onSeek(v.round())
                                  : null,
                            ),
                          ),
                          Row(
                            mainAxisAlignment:
                                MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                _formatMs(position.inMilliseconds),
                                style: theme.textTheme.bodySmall,
                              ),
                              Text(
                                _formatMs(duration.inMilliseconds),
                                style: theme.textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: AppSpacing.md),
          VFButton(
            label: 'Descargar',
            variant: VFButtonVariant.secondary,
            leadingIcon: Icons.download_outlined,
            expand: true,
            onPressed: onDownload,
          ),
        ],
      ),
    );
  }

  String _formatMs(int ms) {
    final seconds = ms ~/ 1000;
    final minutes = seconds ~/ 60;
    final secs = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }
}
