import 'package:flutter/widgets.dart';

import 'config/app_config.dart';
import 'network/api_client.dart';
import 'repositories/auth_repository.dart';
import 'repositories/conversion_repository.dart';
import 'repositories/voice_repository.dart';
import 'session/session_controller.dart';

class VoiceForgeScope extends InheritedNotifier<SessionController> {
  const VoiceForgeScope({
    super.key,
    required super.notifier,
    required this.authRepository,
    required this.voiceRepository,
    required this.conversionRepository,
    required super.child,
  });

  final AuthRepository authRepository;
  final VoiceRepository voiceRepository;
  final ConversionRepository conversionRepository;

  static VoiceForgeScope of(BuildContext context) {
    final scope =
        context.dependOnInheritedWidgetOfExactType<VoiceForgeScope>();
    assert(scope != null, 'VoiceForgeScope no está disponible en este contexto.');
    return scope!;
  }

  static VoiceForgeScope read(BuildContext context) {
    final element =
        context.getElementForInheritedWidgetOfExactType<VoiceForgeScope>();
    final widget = element?.widget;
    assert(
      widget is VoiceForgeScope,
      'VoiceForgeScope no está disponible en este contexto.',
    );
    return widget! as VoiceForgeScope;
  }
}

class VoiceForgeDependencies {
  VoiceForgeDependencies._();

  static ({
    ApiClient apiClient,
    AuthRepository authRepository,
    VoiceRepository voiceRepository,
    ConversionRepository conversionRepository,
  }) create({
    required SessionController sessionController,
  }) {
    final apiClient = ApiClient(
      baseUri: AppConfig.apiBaseUri,
      tokenProvider: () => sessionController.accessToken,
      onUnauthorized: sessionController.clearSession,
    );
    final authRepository = AuthRepository(apiClient);
    final voiceRepository = VoiceRepository(apiClient);
    final conversionRepository = ConversionRepository(apiClient);
    return (
      apiClient: apiClient,
      authRepository: authRepository,
      voiceRepository: voiceRepository,
      conversionRepository: conversionRepository,
    );
  }
}
