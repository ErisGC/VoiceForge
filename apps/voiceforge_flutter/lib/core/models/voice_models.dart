class VoiceProfile {
  const VoiceProfile({
    required this.id,
    required this.userId,
    required this.name,
    required this.description,
    required this.preferredBackend,
    required this.status,
    required this.consentConfirmed,
    required this.totalDurationSeconds,
    required this.clipCount,
    required this.noiseScore,
    required this.diversityScore,
    required this.sampleRate,
    required this.readinessScore,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String userId;
  final String name;
  final String? description;
  final String preferredBackend;
  final String status;
  final bool consentConfirmed;
  final double totalDurationSeconds;
  final int clipCount;
  final double noiseScore;
  final double diversityScore;
  final int sampleRate;
  final double readinessScore;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory VoiceProfile.fromJson(Map<String, dynamic> json) {
    return VoiceProfile(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      preferredBackend: json['preferred_backend'] as String,
      status: json['status'] as String,
      consentConfirmed: json['consent_confirmed'] as bool? ?? false,
      totalDurationSeconds:
          (json['total_duration_seconds'] as num?)?.toDouble() ?? 0,
      clipCount: json['clip_count'] as int? ?? 0,
      noiseScore: (json['noise_score'] as num?)?.toDouble() ?? 0,
      diversityScore: (json['diversity_score'] as num?)?.toDouble() ?? 0,
      sampleRate: json['sample_rate'] as int? ?? 0,
      readinessScore: (json['readiness_score'] as num?)?.toDouble() ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}

class VoiceSample {
  const VoiceSample({
    required this.id,
    required this.voiceProfileId,
    required this.storageBucket,
    required this.storageKey,
    required this.originalFilename,
    required this.contentType,
    required this.sizeBytes,
    required this.durationSeconds,
    required this.sampleRate,
    required this.channels,
    required this.source,
    required this.processingStatus,
    required this.noiseScore,
    required this.diversityScore,
    required this.vadSegments,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String voiceProfileId;
  final String storageBucket;
  final String storageKey;
  final String originalFilename;
  final String contentType;
  final int sizeBytes;
  final double durationSeconds;
  final int sampleRate;
  final int channels;
  final String source;
  final String processingStatus;
  final double noiseScore;
  final double diversityScore;
  final List<Map<String, dynamic>>? vadSegments;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory VoiceSample.fromJson(Map<String, dynamic> json) {
    return VoiceSample(
      id: json['id'] as String,
      voiceProfileId: json['voice_profile_id'] as String,
      storageBucket: json['storage_bucket'] as String,
      storageKey: json['storage_key'] as String,
      originalFilename: json['original_filename'] as String,
      contentType: json['content_type'] as String,
      sizeBytes: json['size_bytes'] as int? ?? 0,
      durationSeconds: (json['duration_seconds'] as num?)?.toDouble() ?? 0,
      sampleRate: json['sample_rate'] as int? ?? 0,
      channels: json['channels'] as int? ?? 0,
      source: json['source'] as String,
      processingStatus: json['processing_status'] as String,
      noiseScore: (json['noise_score'] as num?)?.toDouble() ?? 0,
      diversityScore: (json['diversity_score'] as num?)?.toDouble() ?? 0,
      vadSegments: (json['vad_segments'] as List?)
          ?.map((item) => Map<String, dynamic>.from(item as Map))
          .toList(),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
