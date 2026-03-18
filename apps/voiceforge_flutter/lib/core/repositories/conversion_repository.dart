import 'dart:typed_data';

import '../files/audio_upload_file.dart';
import '../models/conversion_models.dart';
import '../network/api_client.dart';

class ConversionRepository {
  const ConversionRepository(this._client);

  final ApiClient _client;

  Future<List<ConversionJob>> listJobs() async {
    final json = await _client.getJson('conversion-jobs') as List<dynamic>;
    return json
        .map((item) => ConversionJob.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<ConversionJob> getJob(String jobId) async {
    final json =
        await _client.getJson('conversion-jobs/$jobId') as Map<String, dynamic>;
    return ConversionJob.fromJson(json);
  }

  Future<List<ConvertedAudio>> getOutputs(String jobId) async {
    final json =
        await _client.getJson('conversion-jobs/$jobId/outputs') as List<dynamic>;
    return json
        .map((item) => ConvertedAudio.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<ConversionJob> createJob({
    required String voiceProfileId,
    required String mode,
    String? backend,
    required AudioUploadFile file,
  }) async {
    final json = await _client.postMultipart(
      'conversion-jobs',
      fields: {
        'voice_profile_id': voiceProfileId,
        'mode': mode,
        if (backend != null && backend.isNotEmpty) 'backend': backend,
      },
      file: file,
    ) as Map<String, dynamic>;
    return ConversionJob.fromJson(json);
  }

  Future<ConversionJob> processNow(String jobId) async {
    final json = await _client.postJson(
      'conversion-jobs/$jobId/process-now',
      body: const {},
    ) as Map<String, dynamic>;
    return ConversionJob.fromJson(json);
  }

  Future<Uint8List> downloadOutput({
    required String jobId,
    required String outputId,
  }) {
    return _client.getBytes('conversion-jobs/$jobId/outputs/$outputId/download');
  }
}
