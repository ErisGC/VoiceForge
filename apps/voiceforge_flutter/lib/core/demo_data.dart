class VoiceProfileSummary {
  const VoiceProfileSummary({
    required this.id,
    required this.name,
    required this.backend,
    required this.readinessScore,
    required this.clipCount,
    required this.durationLabel,
    required this.noiseLabel,
    required this.modeHint,
  });

  final String id;
  final String name;
  final String backend;
  final double readinessScore;
  final int clipCount;
  final String durationLabel;
  final String noiseLabel;
  final String modeHint;
}

class ConversionJobSummary {
  const ConversionJobSummary({
    required this.id,
    required this.voiceName,
    required this.backend,
    required this.mode,
    required this.status,
    required this.createdLabel,
    required this.durationLabel,
  });

  final String id;
  final String voiceName;
  final String backend;
  final String mode;
  final String status;
  final String createdLabel;
  final String durationLabel;
}

class DemoData {
  static const savedVoices = [
    VoiceProfileSummary(
      id: 'nora',
      name: 'Nora Studio',
      backend: 'Seed-VC',
      readinessScore: 92,
      clipCount: 28,
      durationLabel: '14m 25s',
      noiseLabel: 'Noise 0.11',
      modeHint:
          'Ideal para resultados de alta calidad con una identidad vocal sólida.',
    ),
    VoiceProfileSummary(
      id: 'atlas',
      name: 'Atlas Live',
      backend: 'RVC',
      readinessScore: 78,
      clipCount: 16,
      durationLabel: '08m 10s',
      noiseLabel: 'Noise 0.18',
      modeHint:
          'Pensada para un uso equilibrado con buena velocidad y claridad.',
    ),
    VoiceProfileSummary(
      id: 'iris',
      name: 'Iris Experimental',
      backend: 'OpenVoice',
      readinessScore: 61,
      clipCount: 9,
      durationLabel: '04m 42s',
      noiseLabel: 'Noise 0.26',
      modeHint:
          'Útil para pruebas rápidas y exploración antes de consolidar una voz.',
    ),
  ];

  static const conversionHistory = [
    ConversionJobSummary(
      id: 'job-8401',
      voiceName: 'Nora Studio',
      backend: 'Seed-VC',
      mode: 'Alta calidad',
      status: 'Listo',
      createdLabel: 'Hoy, 09:40',
      durationLabel: '01m 22s',
    ),
    ConversionJobSummary(
      id: 'job-8394',
      voiceName: 'Atlas Live',
      backend: 'RVC',
      mode: 'Equilibrado',
      status: 'En cola',
      createdLabel: 'Hoy, 08:55',
      durationLabel: '00m 18s',
    ),
    ConversionJobSummary(
      id: 'job-8380',
      voiceName: 'Iris Experimental',
      backend: 'OpenVoice',
      mode: 'Rápido',
      status: 'Listo',
      createdLabel: 'Ayer',
      durationLabel: '02m 04s',
    ),
  ];

  static VoiceProfileSummary getVoice(String voiceId) {
    return savedVoices.firstWhere((voice) => voice.id == voiceId);
  }

  static ConversionJobSummary getJob(String jobId) {
    return conversionHistory.firstWhere((job) => job.id == jobId);
  }
}
