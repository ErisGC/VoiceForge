class AuthToken {
  const AuthToken({
    required this.accessToken,
    required this.tokenType,
    required this.expiresInSeconds,
  });

  final String accessToken;
  final String tokenType;
  final int expiresInSeconds;

  factory AuthToken.fromJson(Map<String, dynamic> json) {
    return AuthToken(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
      expiresInSeconds: json['expires_in_seconds'] as int? ?? 0,
    );
  }
}

class AppUser {
  const AppUser({
    required this.id,
    required this.email,
    required this.displayName,
    required this.role,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String email;
  final String displayName;
  final String role;
  final bool isActive;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: json['id'] as String,
      email: json['email'] as String,
      displayName: json['display_name'] as String,
      role: json['role'] as String,
      isActive: json['is_active'] as bool? ?? true,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
