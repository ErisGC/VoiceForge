class ConversionJob {
  const ConversionJob({
    required this.id,
    required this.userId,
    required this.voiceProfileId,
    required this.backend,
    required this.mode,
    required this.status,
    required this.queueName,
    required this.sourceAudioBucket,
    required this.sourceAudioStorageKey,
    required this.sourceAudioFilename,
    required this.sourceAudioContentType,
    required this.sourceAudioDurationSeconds,
    required this.sourceAudioDurationMs,
    required this.sourceAudioSampleRate,
    required this.referenceAudioDurationMs,
    required this.outputAudioDurationMs,
    required this.readinessSnapshot,
    required this.traceabilityToken,
    required this.profilingJson,
    required this.errorCategory,
    required this.errorMessage,
    required this.processingStartedAt,
    required this.processingFinishedAt,
    required this.processingDurationMs,
    required this.startedAt,
    required this.completedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String userId;
  final String voiceProfileId;
  final String backend;
  final String mode;
  final String status;
  final String queueName;
  final String sourceAudioBucket;
  final String sourceAudioStorageKey;
  final String sourceAudioFilename;
  final String sourceAudioContentType;
  final double sourceAudioDurationSeconds;
  final int sourceAudioDurationMs;
  final int sourceAudioSampleRate;
  final int? referenceAudioDurationMs;
  final int? outputAudioDurationMs;
  final double readinessSnapshot;
  final String? traceabilityToken;
  final Map<String, dynamic>? profilingJson;
  final String? errorCategory;
  final String? errorMessage;
  final DateTime? processingStartedAt;
  final DateTime? processingFinishedAt;
  final int? processingDurationMs;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory ConversionJob.fromJson(Map<String, dynamic> json) {
    return ConversionJob(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      voiceProfileId: json['voice_profile_id'] as String,
      backend: json['backend'] as String,
      mode: json['mode'] as String,
      status: json['status'] as String,
      queueName: json['queue_name'] as String,
      sourceAudioBucket: json['source_audio_bucket'] as String,
      sourceAudioStorageKey: json['source_audio_storage_key'] as String,
      sourceAudioFilename: json['source_audio_filename'] as String,
      sourceAudioContentType: json['source_audio_content_type'] as String,
      sourceAudioDurationSeconds:
          (json['source_audio_duration_seconds'] as num?)?.toDouble() ?? 0,
      sourceAudioDurationMs: json['source_audio_duration_ms'] as int? ?? 0,
      sourceAudioSampleRate: json['source_audio_sample_rate'] as int? ?? 0,
      referenceAudioDurationMs: json['reference_audio_duration_ms'] as int?,
      outputAudioDurationMs: json['output_audio_duration_ms'] as int?,
      readinessSnapshot:
          (json['readiness_snapshot'] as num?)?.toDouble() ?? 0,
      traceabilityToken: json['traceability_token'] as String?,
      profilingJson:
          (json['profiling_json'] as Map?)?.cast<String, dynamic>(),
      errorCategory: json['error_category'] as String?,
      errorMessage: json['error_message'] as String?,
      processingStartedAt: _readDateTime(json['processing_started_at']),
      processingFinishedAt: _readDateTime(json['processing_finished_at']),
      processingDurationMs: json['processing_duration_ms'] as int?,
      startedAt: _readDateTime(json['started_at']),
      completedAt: _readDateTime(json['completed_at']),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  static DateTime? _readDateTime(Object? value) {
    if (value is String && value.isNotEmpty) {
      return DateTime.parse(value);
    }
    return null;
  }
}

class ConvertedAudio {
  const ConvertedAudio({
    required this.id,
    required this.conversionJobId,
    required this.storageBucket,
    required this.storageKey,
    required this.format,
    required this.durationSeconds,
    required this.sampleRate,
    required this.sizeBytes,
    required this.watermarkStatus,
    required this.traceabilityMetadata,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String conversionJobId;
  final String storageBucket;
  final String storageKey;
  final String format;
  final double durationSeconds;
  final int sampleRate;
  final int sizeBytes;
  final String watermarkStatus;
  final Map<String, dynamic>? traceabilityMetadata;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory ConvertedAudio.fromJson(Map<String, dynamic> json) {
    return ConvertedAudio(
      id: json['id'] as String,
      conversionJobId: json['conversion_job_id'] as String,
      storageBucket: json['storage_bucket'] as String,
      storageKey: json['storage_key'] as String,
      format: json['format'] as String,
      durationSeconds: (json['duration_seconds'] as num?)?.toDouble() ?? 0,
      sampleRate: json['sample_rate'] as int? ?? 0,
      sizeBytes: json['size_bytes'] as int? ?? 0,
      watermarkStatus: json['watermark_status'] as String? ?? 'pending',
      traceabilityMetadata:
          (json['traceability_metadata'] as Map?)?.cast<String, dynamic>(),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
