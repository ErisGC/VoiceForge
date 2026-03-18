import 'package:flutter/foundation.dart';

import '../models/auth_models.dart';
import '../repositories/auth_repository.dart';

class SessionController extends ChangeNotifier {
  SessionController({required AuthRepository authRepository})
      : _authRepository = authRepository;

  final AuthRepository _authRepository;

  String? _accessToken;
  AppUser? _currentUser;
  bool _isBusy = false;
  String? _errorMessage;
  final Map<String, String> _jobPresetLabels = {};

  String? get accessToken => _accessToken;
  AppUser? get currentUser => _currentUser;
  bool get isBusy => _isBusy;
  bool get isAuthenticated => _accessToken != null && _currentUser != null;
  String? get errorMessage => _errorMessage;

  Future<void> login({
    required String email,
    required String password,
  }) async {
    await _runAuth(() async {
      final token = await _authRepository.login(email: email, password: password);
      _accessToken = token.accessToken;
      _currentUser = await _authRepository.getMe();
    });
  }

  Future<void> register({
    required String displayName,
    required String email,
    required String password,
  }) async {
    await _runAuth(() async {
      final token = await _authRepository.register(
        displayName: displayName,
        email: email,
        password: password,
      );
      _accessToken = token.accessToken;
      _currentUser = await _authRepository.getMe();
    });
  }

  void clearSession() {
    _accessToken = null;
    _currentUser = null;
    _jobPresetLabels.clear();
    notifyListeners();
  }

  void rememberJobPreset(String jobId, String presetLabel) {
    _jobPresetLabels[jobId] = presetLabel;
  }

  String? presetForJob(String jobId) => _jobPresetLabels[jobId];

  Future<void> _runAuth(Future<void> Function() action) async {
    _isBusy = true;
    _errorMessage = null;
    notifyListeners();
    try {
      await action();
    } catch (error) {
      _accessToken = null;
      _currentUser = null;
      _errorMessage = error.toString().replaceFirst('ApiException: ', '');
      rethrow;
    } finally {
      _isBusy = false;
      notifyListeners();
    }
  }
}
