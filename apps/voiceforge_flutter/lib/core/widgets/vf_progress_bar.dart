import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';
import '../../app/design_system/app_typography.dart';

class VFProgressBar extends StatelessWidget {
  const VFProgressBar({
    super.key,
    required this.value,
    this.label,
    this.trailing,
    this.height = 10,
  });

  final double value;
  final String? label;
  final String? trailing;
  final double height;

  @override
  Widget build(BuildContext context) {
    final clamped = value.clamp(0, 1);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null || trailing != null)
          Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.xs),
            child: Row(
              children: [
                if (label != null)
                  Expanded(
                    child: Text(label!, style: AppTypography.labelMedium),
                  ),
                if (trailing != null)
                  Text(
                    trailing!,
                    style: AppTypography.labelMedium.copyWith(
                      color: AppColors.primary400,
                    ),
                  ),
              ],
            ),
          ),
        ClipRRect(
          borderRadius: AppRadius.pill,
          child: Container(
            height: height,
            color: AppColors.surface700,
            child: FractionallySizedBox(
              widthFactor: clamped.toDouble(),
              alignment: Alignment.centerLeft,
              child: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [AppColors.primary500, AppColors.accentCyan],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
