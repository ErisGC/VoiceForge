import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';
import '../../app/design_system/app_typography.dart';

enum VFChipTone { recommended, success, warning, error, neutral }

class VFChip extends StatelessWidget {
  const VFChip({
    super.key,
    required this.label,
    this.tone = VFChipTone.neutral,
    this.icon,
  });

  final String label;
  final VFChipTone tone;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final style = _style(tone);
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: style.background,
        borderRadius: AppRadius.pill,
        border: Border.all(color: style.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 14, color: style.foreground),
            const SizedBox(width: AppSpacing.xxs),
          ],
          Text(
            label,
            style: AppTypography.labelSmall.copyWith(color: style.foreground),
          ),
        ],
      ),
    );
  }

  _ChipStyle _style(VFChipTone tone) {
    return switch (tone) {
      VFChipTone.recommended => const _ChipStyle(
        background: Color(0x226D7CFF),
        border: Color(0x4D8592FF),
        foreground: AppColors.primary400,
      ),
      VFChipTone.success => const _ChipStyle(
        background: Color(0x1F3DDC97),
        border: Color(0x4D3DDC97),
        foreground: AppColors.success500,
      ),
      VFChipTone.warning => const _ChipStyle(
        background: Color(0x1FFFB84D),
        border: Color(0x4DFFB84D),
        foreground: AppColors.warning500,
      ),
      VFChipTone.error => const _ChipStyle(
        background: Color(0x1FFF6B7A),
        border: Color(0x4DFF6B7A),
        foreground: AppColors.danger500,
      ),
      VFChipTone.neutral => const _ChipStyle(
        background: AppColors.surface700,
        border: AppColors.borderSoft,
        foreground: AppColors.text300,
      ),
    };
  }
}

class _ChipStyle {
  const _ChipStyle({
    required this.background,
    required this.border,
    required this.foreground,
  });

  final Color background;
  final Color border;
  final Color foreground;
}
