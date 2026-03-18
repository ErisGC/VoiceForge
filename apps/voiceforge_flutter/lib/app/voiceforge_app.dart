import 'package:flutter/material.dart';

import 'router.dart';
import '../core/config/app_config.dart';
import '../core/network/api_client.dart';
import '../core/repositories/auth_repository.dart';
import '../core/repositories/conversion_repository.dart';
import '../core/repositories/voice_repository.dart';
import '../core/session/session_controller.dart';
import '../core/voiceforge_scope.dart';
import 'theme.dart';

class VoiceForgeApp extends StatefulWidget {
  const VoiceForgeApp({super.key});

  @override
  State<VoiceForgeApp> createState() => _VoiceForgeAppState();
}

class _VoiceForgeAppState extends State<VoiceForgeApp> {
  late final ApiClient _apiClient = ApiClient(
    baseUri: AppConfig.apiBaseUri,
    tokenProvider: () => _sessionController.accessToken,
    onUnauthorized: _sessionController.clearSession,
  );
  late final AuthRepository _authRepository = AuthRepository(_apiClient);
  late final VoiceRepository _voiceRepository = VoiceRepository(_apiClient);
  late final ConversionRepository _conversionRepository =
      ConversionRepository(_apiClient);
  late final SessionController _sessionController =
      SessionController(authRepository: _authRepository);

  @override
  Widget build(BuildContext context) {
    return VoiceForgeScope(
      notifier: _sessionController,
      authRepository: _authRepository,
      voiceRepository: _voiceRepository,
      conversionRepository: _conversionRepository,
      child: MaterialApp.router(
        title: 'VoiceForge',
        debugShowCheckedModeBanner: false,
        theme: buildVoiceForgeTheme(),
        routerConfig: router,
      ),
    );
  }
}
