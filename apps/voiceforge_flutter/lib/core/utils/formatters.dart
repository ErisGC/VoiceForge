String formatDurationSeconds(num seconds) {
  final totalSeconds = seconds.round();
  if (totalSeconds <= 0) {
    return '0s';
  }
  final minutes = totalSeconds ~/ 60;
  final remainingSeconds = totalSeconds % 60;
  if (minutes == 0) {
    return '${remainingSeconds}s';
  }
  return '${minutes}m ${remainingSeconds.toString().padLeft(2, '0')}s';
}

String formatFileSize(int bytes) {
  if (bytes < 1024) {
    return '${bytes} B';
  }
  if (bytes < 1024 * 1024) {
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }
  return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
}

String formatRelativeDate(DateTime dateTime) {
  final now = DateTime.now();
  final local = dateTime.toLocal();
  final difference = now.difference(local);
  if (difference.inDays == 0) {
    return 'Hoy, ${_two(local.hour)}:${_two(local.minute)}';
  }
  if (difference.inDays == 1) {
    return 'Ayer';
  }
  return '${_two(local.day)}/${_two(local.month)}/${local.year}';
}

String formatStatusLabel(String status) {
  return switch (status) {
    'ready' || 'active' || 'completed' => 'Listo',
    'queued' || 'pending' => 'En cola',
    'processing' || 'running' => 'En proceso',
    'failed' => 'Fallido',
    'training' => 'Preparando',
    'draft' => 'Borrador',
    'archived' => 'Archivado',
    _ => 'Activo',
  };
}

String formatSampleSource(String source) {
  return switch (source) {
    'microphone' => 'Micrófono',
    'import' => 'Importado',
    _ => 'Archivo',
  };
}

String formatModeLabel(String mode) {
  return switch (mode) {
    'live' => 'Rápido',
    _ => 'Alta calidad',
  };
}

String readinessHeadline(double score) {
  if (score >= 85) {
    return 'Lista para resultados consistentes';
  }
  if (score >= 65) {
    return 'Buen punto de partida';
  }
  return 'Necesita más material';
}

String readinessHint({
  required double score,
  required int clipCount,
}) {
  if (clipCount == 0) {
    return 'Añade tus primeras muestras para empezar a construir la identidad vocal.';
  }
  if (score >= 85) {
    return 'La identidad vocal ya se ve sólida. Añade más muestras si quieres cubrir más matices.';
  }
  if (score >= 65) {
    return 'Añade más muestras para mejorar la identidad vocal y hacerla más estable.';
  }
  return 'Todavía faltan muestras limpias y variadas para reforzar la identidad vocal.';
}

String describeNoise(double score) {
  if (score <= 0.12) {
    return 'Ruido bajo';
  }
  if (score <= 0.22) {
    return 'Ruido moderado';
  }
  return 'Revisar limpieza';
}

String describeDiversity(double score) {
  if (score >= 0.6) {
    return 'Buena variedad';
  }
  if (score >= 0.35) {
    return 'Variedad media';
  }
  return 'Variedad limitada';
}

String _two(int value) => value.toString().padLeft(2, '0');
