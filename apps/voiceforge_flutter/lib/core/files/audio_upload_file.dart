import 'dart:typed_data';

class AudioUploadFile {
  const AudioUploadFile({
    required this.name,
    required this.bytes,
    required this.sizeBytes,
    this.mimeType,
  });

  final String name;
  final Uint8List bytes;
  final int sizeBytes;
  final String? mimeType;
}
