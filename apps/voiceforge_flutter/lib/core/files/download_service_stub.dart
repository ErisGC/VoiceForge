import 'dart:typed_data';

import 'download_service.dart';

class _UnsupportedDownloadService implements DownloadService {
  @override
  Future<DownloadResult> saveBytes({
    required String filename,
    required Uint8List bytes,
    required String contentType,
  }) async {
    return const DownloadResult(
      message: 'La descarga directa no está disponible en esta plataforma.',
    );
  }
}

DownloadService createPlatformDownloadService() => _UnsupportedDownloadService();
