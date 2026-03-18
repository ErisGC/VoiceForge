import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// Real-time job notification service using WebSocket + Redis pub/sub.
///
/// Connects to the backend WebSocket endpoint at `/ws/jobs?token=<jwt>` and
/// forwards incoming job-status messages to a broadcast [Stream].
class JobNotificationService extends ChangeNotifier {
  JobNotificationService({required this.baseWsUrl});

  /// Base WebSocket URL (e.g. `ws://localhost:8000`).
  final String baseWsUrl;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;

  final StreamController<JobNotification> _controller =
      StreamController<JobNotification>.broadcast();

  /// Stream of incoming job notification events.
  Stream<JobNotification> get notifications => _controller.stream;

  bool _connected = false;

  /// Whether the WebSocket is currently connected.
  bool get isConnected => _connected;

  /// Connect to the WebSocket endpoint with the given JWT [token].
  void connect(String token) {
    disconnect();
    final uri = Uri.parse('$baseWsUrl/ws/jobs?token=$token');
    _channel = WebSocketChannel.connect(uri);
    _connected = true;
    notifyListeners();

    _subscription = _channel!.stream.listen(
      _onMessage,
      onError: _onError,
      onDone: _onDone,
    );
  }

  /// Gracefully disconnect the WebSocket.
  void disconnect() {
    _subscription?.cancel();
    _subscription = null;
    _channel?.sink.close();
    _channel = null;
    if (_connected) {
      _connected = false;
      notifyListeners();
    }
  }

  void _onMessage(dynamic raw) {
    try {
      final data = raw is String ? jsonDecode(raw) as Map<String, dynamic> : <String, dynamic>{};
      final type = data['type'] as String? ?? '';
      if (type == 'job_update') {
        final payload = data['payload'] as Map<String, dynamic>? ?? {};
        _controller.add(JobNotification.fromJson(payload));
      }
    } catch (e) {
      debugPrint('JobNotificationService: failed to parse message: $e');
    }
  }

  void _onError(Object error) {
    debugPrint('JobNotificationService: error: $error');
    _connected = false;
    notifyListeners();
  }

  void _onDone() {
    _connected = false;
    notifyListeners();
  }

  @override
  void dispose() {
    disconnect();
    _controller.close();
    super.dispose();
  }
}

/// A single job notification event received from the server.
class JobNotification {
  const JobNotification({
    required this.jobId,
    required this.status,
    this.progress,
    this.message,
  });

  factory JobNotification.fromJson(Map<String, dynamic> json) {
    return JobNotification(
      jobId: json['job_id'] as String? ?? '',
      status: json['status'] as String? ?? 'unknown',
      progress: (json['progress'] as num?)?.toDouble(),
      message: json['message'] as String?,
    );
  }

  final String jobId;
  final String status;
  final double? progress;
  final String? message;
}
