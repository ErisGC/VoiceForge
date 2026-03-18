import 'package:flutter/material.dart';

import 'vf_chip.dart';

class VFStatusBadge extends StatelessWidget {
  const VFStatusBadge({super.key, required this.label, this.icon, this.tone});

  final String label;
  final IconData? icon;
  final VFChipTone? tone;

  factory VFStatusBadge.fromStatus(String status) {
    final normalized = status.trim().toLowerCase();
    final badgeTone = switch (normalized) {
      'completed' ||
      'ready' ||
      'active' ||
      'listo' ||
      'lista' => VFChipTone.success,
      'queued' ||
      'processing' ||
      'running' ||
      'en cola' ||
      'en proceso' => VFChipTone.warning,
      'failed' || 'error' || 'fallido' => VFChipTone.error,
      'recommended' || 'recomendado' => VFChipTone.recommended,
      _ => VFChipTone.neutral,
    };
    final badgeIcon = switch (badgeTone) {
      VFChipTone.success => Icons.check_circle_outline,
      VFChipTone.warning => Icons.schedule_outlined,
      VFChipTone.error => Icons.error_outline,
      VFChipTone.recommended => Icons.auto_awesome,
      VFChipTone.neutral => Icons.circle_outlined,
    };
    return VFStatusBadge(label: status, tone: badgeTone, icon: badgeIcon);
  }

  @override
  Widget build(BuildContext context) {
    return VFChip(label: label, tone: tone ?? VFChipTone.neutral, icon: icon);
  }
}
