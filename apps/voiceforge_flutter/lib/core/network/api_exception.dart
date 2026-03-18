class ApiException implements Exception {
  const ApiException({
    required this.message,
    this.statusCode,
    this.details,
    this.isNetworkError = false,
  });

  final String message;
  final int? statusCode;
  final Object? details;
  final bool isNetworkError;

  bool get isUnauthorized => statusCode == 401 || statusCode == 403;

  @override
  String toString() => 'ApiException(statusCode: $statusCode, message: $message)';
}
