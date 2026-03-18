import 'package:flutter/foundation.dart';

class AppConfig {
  static const _configuredApiBaseUrl = String.fromEnvironment(
    'VOICEFORGE_API_BASE_URL',
    defaultValue: '',
  );
  static const _demoFallbackValue = String.fromEnvironment(
    'VOICEFORGE_DEMO_FALLBACK',
    defaultValue: 'false',
  );

  static Uri get apiBaseUri {
    if (_configuredApiBaseUrl.trim().isNotEmpty) {
      return _normalize(Uri.parse(_configuredApiBaseUrl.trim()));
    }

    if (kIsWeb) {
      return _normalize(Uri.parse('http://localhost:8000/api/v1'));
    }

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return _normalize(Uri.parse('http://10.0.2.2:8000/api/v1'));
      default:
        return _normalize(Uri.parse('http://localhost:8000/api/v1'));
    }
  }

  static bool get demoFallbackEnabled {
    return _demoFallbackValue.toLowerCase() == 'true';
  }

  static Uri _normalize(Uri value) {
    final path = value.path.endsWith('/') ? value.path : '${value.path}/';
    return value.replace(path: path);
  }
}
