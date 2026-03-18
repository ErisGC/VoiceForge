import '../files/audio_upload_file.dart';
import '../models/voice_models.dart';
import '../network/api_client.dart';

class VoiceRepository {
  const VoiceRepository(this._client);

  final ApiClient _client;

  Future<List<VoiceProfile>> listProfiles() async {
    final json = await _client.getJson('voice-profiles') as List<dynamic>;
    return json
        .map((item) => VoiceProfile.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<VoiceProfile> getProfile(String profileId) async {
    final json =
        await _client.getJson('voice-profiles/$profileId') as Map<String, dynamic>;
    return VoiceProfile.fromJson(json);
  }

  Future<VoiceProfile> createProfile({
    required String name,
    required String description,
  }) async {
    final json = await _client.postJson(
      'voice-profiles',
      body: {
        'name': name,
        'description': description.isEmpty ? null : description,
        'preferred_backend': 'seed_vc',
        'consent_confirmed': true,
        'consent_text':
            'El usuario confirma que cuenta con consentimiento explícito para crear este perfil de voz.',
        'consent_evidence_storage_key': null,
      },
    ) as Map<String, dynamic>;
    return VoiceProfile.fromJson(json);
  }

  Future<List<VoiceSample>> listSamples(String profileId) async {
    final json =
        await _client.getJson('voice-profiles/$profileId/samples') as List<dynamic>;
    return json
        .map((item) => VoiceSample.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<VoiceSample> uploadSample({
    required String profileId,
    required AudioUploadFile file,
    required String source,
  }) async {
    final json = await _client.postMultipart(
      'voice-profiles/$profileId/samples',
      fields: {'source': source},
      file: file,
    ) as Map<String, dynamic>;
    return VoiceSample.fromJson(json);
  }
}
