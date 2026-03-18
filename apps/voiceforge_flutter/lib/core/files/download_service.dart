import 'dart:typed_data';

import 'download_service_stub.dart'
    if (dart.library.io) 'download_service_io.dart'
    if (dart.library.html) 'download_service_web.dart';

class DownloadResult {
  const DownloadResult({
    required this.message,
    this.savedLocation,
  });

  final String message;
  final String? savedLocation;
}

abstract class DownloadService {
  Future<DownloadResult> saveBytes({
    required String filename,
    required Uint8List bytes,
    required String contentType,
  });
}

DownloadService createDownloadService() => createPlatformDownloadService();
