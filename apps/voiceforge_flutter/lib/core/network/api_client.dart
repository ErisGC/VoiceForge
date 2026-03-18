import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../files/audio_upload_file.dart';
import 'api_exception.dart';

class ApiClient {
  ApiClient({
    required Uri baseUri,
    http.Client? httpClient,
    this.tokenProvider,
    this.onUnauthorized,
  })  : _baseUri = baseUri,
        _httpClient = httpClient ?? http.Client();

  final Uri _baseUri;
  final http.Client _httpClient;
  final String? Function()? tokenProvider;
  final VoidCallback? onUnauthorized;

  Future<dynamic> getJson(String path, {bool authenticated = true}) async {
    try {
      final response = await _httpClient.get(
        _resolve(path),
        headers: _headers(authenticated: authenticated),
      );
      return _decodeResponse(response);
    } on SocketException catch (error) {
      throw ApiException(
        message: 'No fue posible conectar con el backend.',
        details: error,
        isNetworkError: true,
      );
    }
  }

  Future<dynamic> postJson(
    String path, {
    required Map<String, dynamic> body,
    bool authenticated = true,
  }) async {
    try {
      final response = await _httpClient.post(
        _resolve(path),
        headers: _headers(
          authenticated: authenticated,
          contentType: 'application/json',
        ),
        body: jsonEncode(body),
      );
      return _decodeResponse(response);
    } on SocketException catch (error) {
      throw ApiException(
        message: 'No fue posible conectar con el backend.',
        details: error,
        isNetworkError: true,
      );
    }
  }

  Future<dynamic> postMultipart(
    String path, {
    required Map<String, String> fields,
    required AudioUploadFile file,
    bool authenticated = true,
    String fileField = 'file',
  }) async {
    try {
      final request = http.MultipartRequest('POST', _resolve(path))
        ..headers.addAll(_headers(authenticated: authenticated))
        ..fields.addAll(fields)
        ..files.add(
          http.MultipartFile.fromBytes(
            fileField,
            file.bytes,
            filename: file.name,
          ),
        );

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);
      return _decodeResponse(response);
    } on SocketException catch (error) {
      throw ApiException(
        message: 'No fue posible conectar con el backend.',
        details: error,
        isNetworkError: true,
      );
    }
  }

  Future<Uint8List> getBytes(String path, {bool authenticated = true}) async {
    try {
      final response = await _httpClient.get(
        _resolve(path),
        headers: _headers(authenticated: authenticated),
      );
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return response.bodyBytes;
      }
      throw _toException(response);
    } on SocketException catch (error) {
      throw ApiException(
        message: 'No fue posible conectar con el backend.',
        details: error,
        isNetworkError: true,
      );
    }
  }

  Uri resolve(String path) => _resolve(path);

  Map<String, String> _headers({
    required bool authenticated,
    String? contentType,
  }) {
    final headers = <String, String>{'Accept': 'application/json'};
    if (contentType != null) {
      headers['Content-Type'] = contentType;
    }
    if (authenticated) {
      final token = tokenProvider?.call();
      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return headers;
  }

  Uri _resolve(String path) {
    final normalized = path.startsWith('/') ? path.substring(1) : path;
    return _baseUri.resolve(normalized);
  }

  dynamic _decodeResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) {
        return null;
      }
      return jsonDecode(response.body);
    }
    throw _toException(response);
  }

  ApiException _toException(http.Response response) {
    dynamic decoded;
    try {
      decoded = response.body.isEmpty ? null : jsonDecode(response.body);
    } catch (_) {
      decoded = response.body;
    }

    final detail = switch (decoded) {
      {'detail': final Object value} => value,
      _ => decoded,
    };
    final message =
        _messageFromDetail(detail) ?? 'La solicitud no se pudo completar.';
    final exception = ApiException(
      message: message,
      statusCode: response.statusCode,
      details: detail,
    );
    if (exception.isUnauthorized) {
      onUnauthorized?.call();
    }
    return exception;
  }

  String? _messageFromDetail(Object? detail) {
    if (detail is String && detail.isNotEmpty) {
      return detail;
    }
    if (detail is List && detail.isNotEmpty) {
      return detail.join(', ');
    }
    if (detail is Map && detail.isNotEmpty) {
      return detail.values.join(', ');
    }
    return null;
  }
}
