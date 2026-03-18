import 'dart:io';
import 'dart:typed_data';

import 'download_service.dart';

class _IoDownloadService implements DownloadService {
  @override
  Future<DownloadResult> saveBytes({
    required String filename,
    required Uint8List bytes,
    required String contentType,
  }) async {
    final safeName = filename.replaceAll(RegExp(r'[^\w\-.]'), '_');
    final directory = Directory(
      '${Directory.systemTemp.path}${Platform.pathSeparator}voiceforge_downloads',
    );
    if (!directory.existsSync()) {
      directory.createSync(recursive: true);
    }
    final file = File('${directory.path}${Platform.pathSeparator}$safeName');
    await file.writeAsBytes(bytes, flush: true);
    return DownloadResult(
      message: 'Resultado guardado en almacenamiento temporal.',
      savedLocation: file.path,
    );
  }
}

DownloadService createPlatformDownloadService() => _IoDownloadService();
