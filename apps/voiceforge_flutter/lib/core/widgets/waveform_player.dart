import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';

/// Extracts normalised amplitude samples from raw audio bytes in a background
/// isolate so that the UI thread stays responsive.
///
/// Returns a [Float32List] of values in the range [0, 1].
Future<Float32List> extractAmplitudes(Uint8List audioBytes, {int barCount = 80}) {
  return compute(_computeAmplitudes, _AmplitudeArgs(audioBytes, barCount));
}

class _AmplitudeArgs {
  const _AmplitudeArgs(this.bytes, this.barCount);
  final Uint8List bytes;
  final int barCount;
}

Float32List _computeAmplitudes(_AmplitudeArgs args) {
  final bytes = args.bytes;
  final barCount = args.barCount;
  // Interpret raw bytes as signed 16-bit PCM (little-endian). For non-PCM
  // formats (MP3, etc.) this produces a "noisy but usable" approximation that
  // is good enough for a visual waveform.
  final sampleCount = bytes.length ~/ 2;
  if (sampleCount == 0) {
    return Float32List(barCount);
  }
  final data = ByteData.sublistView(bytes);
  final samplesPerBar = math.max(1, sampleCount ~/ barCount);
  final result = Float32List(barCount);
  double globalMax = 1;

  for (int bar = 0; bar < barCount; bar++) {
    double sum = 0;
    final start = bar * samplesPerBar;
    final end = math.min(start + samplesPerBar, sampleCount);
    for (int i = start; i < end; i++) {
      final sample = data.getInt16(i * 2, Endian.little).abs();
      sum += sample;
    }
    final avg = sum / (end - start);
    result[bar] = avg;
    if (avg > globalMax) globalMax = avg;
  }

  // Normalise to [0, 1].
  for (int i = 0; i < barCount; i++) {
    result[i] = result[i] / globalMax;
  }
  return result;
}

/// A waveform visualisation with integrated [just_audio] playback.
///
/// Supports seek-by-tap and configurable bar / progress colours.  Amplitudes
/// are extracted in a background isolate via [extractAmplitudes].
class VFWaveformPlayer extends StatefulWidget {
  const VFWaveformPlayer({
    super.key,
    required this.audioSource,
    this.amplitudes,
    this.barCount = 80,
    this.barColor,
    this.progressColor,
    this.backgroundColor,
    this.barWidth = 3.0,
    this.barSpacing = 2.0,
    this.height = 64.0,
  });

  /// The audio source URI to play.
  final String audioSource;

  /// Pre-computed amplitudes. If null the widget shows a placeholder waveform.
  final Float32List? amplitudes;

  /// Number of bars in the waveform.
  final int barCount;

  /// Color of bars that have not been played yet.
  final Color? barColor;

  /// Color of bars already played (progress).
  final Color? progressColor;

  /// Background color of the waveform area.
  final Color? backgroundColor;

  /// Width of each bar in logical pixels.
  final double barWidth;

  /// Spacing between bars in logical pixels.
  final double barSpacing;

  /// Total height of the waveform widget.
  final double height;

  @override
  State<VFWaveformPlayer> createState() => _VFWaveformPlayerState();
}

class _VFWaveformPlayerState extends State<VFWaveformPlayer> {
  late final AudioPlayer _player = AudioPlayer();
  Duration _position = Duration.zero;
  Duration _duration = const Duration(seconds: 1);
  bool _isPlaying = false;
  StreamSubscription<Duration>? _positionSub;
  StreamSubscription<PlayerState>? _stateSub;

  @override
  void initState() {
    super.initState();
    _initPlayer();
  }

  Future<void> _initPlayer() async {
    try {
      final dur = await _player.setUrl(widget.audioSource);
      if (dur != null && mounted) {
        setState(() => _duration = dur);
      }
    } catch (_) {
      // Source not loadable; graceful degradation.
    }
    _positionSub = _player.positionStream.listen((pos) {
      if (mounted) setState(() => _position = pos);
    });
    _stateSub = _player.playerStateStream.listen((state) {
      if (mounted) {
        setState(() => _isPlaying = state.playing);
        if (state.processingState == ProcessingState.completed) {
          _player.seek(Duration.zero);
          _player.pause();
        }
      }
    });
  }

  @override
  void dispose() {
    _positionSub?.cancel();
    _stateSub?.cancel();
    _player.dispose();
    super.dispose();
  }

  void _togglePlayPause() {
    if (_isPlaying) {
      _player.pause();
    } else {
      _player.play();
    }
  }

  void _seekToFraction(double fraction) {
    final target = Duration(
      milliseconds: (_duration.inMilliseconds * fraction).round(),
    );
    _player.seek(target);
  }

  double get _progress {
    if (_duration.inMilliseconds == 0) return 0;
    return (_position.inMilliseconds / _duration.inMilliseconds).clamp(0.0, 1.0);
  }

  @override
  Widget build(BuildContext context) {
    final barColor = widget.barColor ?? AppColors.text500;
    final progressColor = widget.progressColor ?? AppColors.primary500;
    final bgColor = widget.backgroundColor ?? AppColors.surface800;

    return Container(
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: AppRadius.md,
        border: Border.all(color: AppColors.borderSoft),
      ),
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      child: Row(
        children: [
          _PlayPauseButton(
            isPlaying: _isPlaying,
            onPressed: _togglePlayPause,
            color: progressColor,
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: GestureDetector(
              onTapDown: (details) {
                final box = context.findRenderObject() as RenderBox?;
                if (box == null) return;
                // Account for the play button + spacing width.
                final totalBarWidth = box.size.width - 44 - AppSpacing.sm;
                final fraction =
                    (details.localPosition.dx - 44 - AppSpacing.sm) / totalBarWidth;
                _seekToFraction(fraction.clamp(0.0, 1.0));
              },
              child: CustomPaint(
                size: Size(double.infinity, widget.height),
                painter: _WaveformPainter(
                  amplitudes: widget.amplitudes,
                  progress: _progress,
                  barColor: barColor,
                  progressColor: progressColor,
                  barWidth: widget.barWidth,
                  barSpacing: widget.barSpacing,
                  barCount: widget.barCount,
                ),
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.xs),
          SizedBox(
            width: 48,
            child: Text(
              _formatDuration(_position),
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ),
    );
  }

  String _formatDuration(Duration d) {
    final minutes = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }
}

class _PlayPauseButton extends StatelessWidget {
  const _PlayPauseButton({
    required this.isPlaying,
    required this.onPressed,
    required this.color,
  });

  final bool isPlaying;
  final VoidCallback onPressed;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color.withValues(alpha: 0.15),
      shape: const CircleBorder(),
      child: InkWell(
        onTap: onPressed,
        customBorder: const CircleBorder(),
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.xs),
          child: Icon(
            isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded,
            color: color,
            size: 28,
          ),
        ),
      ),
    );
  }
}

class _WaveformPainter extends CustomPainter {
  _WaveformPainter({
    required this.amplitudes,
    required this.progress,
    required this.barColor,
    required this.progressColor,
    required this.barWidth,
    required this.barSpacing,
    required this.barCount,
  });

  final Float32List? amplitudes;
  final double progress;
  final Color barColor;
  final Color progressColor;
  final double barWidth;
  final double barSpacing;
  final int barCount;

  @override
  void paint(Canvas canvas, Size size) {
    final amps = amplitudes ?? Float32List(barCount);
    final count = amps.length;
    if (count == 0) return;

    final totalBarWidth = barWidth + barSpacing;
    final visibleBars = math.min(count, (size.width / totalBarWidth).floor());
    final midY = size.height / 2;
    final maxBarHeight = size.height * 0.85;
    const minBarHeight = 2.0;

    final paintInactive = Paint()
      ..color = barColor
      ..strokeCap = StrokeCap.round
      ..strokeWidth = barWidth;

    final paintActive = Paint()
      ..color = progressColor
      ..strokeCap = StrokeCap.round
      ..strokeWidth = barWidth;

    for (int i = 0; i < visibleBars; i++) {
      final amp = amps[i].clamp(0.0, 1.0);
      final h = math.max(minBarHeight, amp * maxBarHeight);
      final x = i * totalBarWidth + barWidth / 2;
      final fraction = i / visibleBars;
      final paint = fraction <= progress ? paintActive : paintInactive;
      canvas.drawLine(
        Offset(x, midY - h / 2),
        Offset(x, midY + h / 2),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(_WaveformPainter old) {
    return old.progress != progress ||
        old.amplitudes != amplitudes ||
        old.barColor != barColor ||
        old.progressColor != progressColor;
  }
}
