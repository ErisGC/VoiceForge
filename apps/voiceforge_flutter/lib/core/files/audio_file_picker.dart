import 'dart:typed_data';

import 'package:file_selector/file_selector.dart';

import 'audio_upload_file.dart';

class AudioFilePicker {
  static final XTypeGroup _audioTypeGroup = XTypeGroup(
    label: 'audio',
    extensions: const ['wav', 'mp3', 'm4a', 'aac', 'ogg', 'flac'],
    mimeTypes: const [
      'audio/wav',
      'audio/x-wav',
      'audio/mpeg',
      'audio/mp4',
      'audio/aac',
      'audio/ogg',
      'audio/flac',
    ],
    uniformTypeIdentifiers: const ['public.audio'],
  );

  Future<AudioUploadFile?> pickSingleAudio() async {
    final file = await openFile(
      acceptedTypeGroups: [_audioTypeGroup],
      confirmButtonText: 'Seleccionar audio',
    );
    if (file == null) {
      return null;
    }

    final Uint8List bytes = await file.readAsBytes();
    return AudioUploadFile(
      name: file.name,
      bytes: bytes,
      sizeBytes: bytes.lengthInBytes,
      mimeType: _inferMimeType(file.name),
    );
  }

  String? _inferMimeType(String name) {
    final extension = name.split('.').last.toLowerCase();
    return switch (extension) {
      'wav' => 'audio/wav',
      'mp3' => 'audio/mpeg',
      'm4a' => 'audio/mp4',
      'aac' => 'audio/aac',
      'ogg' => 'audio/ogg',
      'flac' => 'audio/flac',
      _ => null,
    };
  }
}
