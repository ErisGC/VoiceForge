import 'dart:html' as html;
import 'dart:typed_data';

import 'download_service.dart';

class _WebDownloadService implements DownloadService {
  @override
  Future<DownloadResult> saveBytes({
    required String filename,
    required Uint8List bytes,
    required String contentType,
  }) async {
    final blob = html.Blob([bytes], contentType);
    final url = html.Url.createObjectUrlFromBlob(blob);
    final anchor = html.AnchorElement(href: url)
      ..download = filename
      ..style.display = 'none';
    html.document.body?.append(anchor);
    anchor.click();
    anchor.remove();
    html.Url.revokeObjectUrl(url);
    return const DownloadResult(
      message: 'La descarga se abrió en el navegador.',
    );
  }
}

DownloadService createPlatformDownloadService() => _WebDownloadService();
