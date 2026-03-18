import '../models/auth_models.dart';
import '../network/api_client.dart';

class AuthRepository {
  const AuthRepository(this._client);

  final ApiClient _client;

  Future<AuthToken> login({
    required String email,
    required String password,
  }) async {
    final json = await _client.postJson(
      'auth/login',
      authenticated: false,
      body: {
        'email': email,
        'password': password,
      },
    ) as Map<String, dynamic>;
    return AuthToken.fromJson(json);
  }

  Future<AuthToken> register({
    required String displayName,
    required String email,
    required String password,
  }) async {
    final json = await _client.postJson(
      'auth/register',
      authenticated: false,
      body: {
        'display_name': displayName,
        'email': email,
        'password': password,
      },
    ) as Map<String, dynamic>;
    return AuthToken.fromJson(json);
  }

  Future<AppUser> getMe() async {
    final json = await _client.getJson('users/me') as Map<String, dynamic>;
    return AppUser.fromJson(json);
  }
}
