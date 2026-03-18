import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_gradients.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';
import 'vf_chip.dart';
import 'vf_panel.dart';

class VFWaveformContainer extends StatelessWidget {
  const VFWaveformContainer({
    super.key,
    this.title,
    this.caption,
    this.height = 180,
    this.trailing,
  });

  final String? title;
  final String? caption;
  final double height;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    const bars = [
      0.18,
      0.42,
      0.76,
      0.52,
      0.66,
      0.28,
      0.84,
      0.44,
      0.62,
      0.34,
      0.79,
      0.49,
      0.58,
      0.31,
    ];

    return VFPanel(
      variant: VFPanelVariant.hero,
      padding: const EdgeInsets.all(AppSpacing.xl),
      gradient: AppGradients.hero,
      child: SizedBox(
        height: height,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (title != null || trailing != null)
              Row(
                children: [
                  if (title != null)
                    Expanded(
                      child: Text(
                        title!,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ...?(trailing == null ? null : <Widget>[trailing!]),
                ],
              ),
            if (caption != null) ...[
              const SizedBox(height: AppSpacing.xs),
              Text(caption!, style: Theme.of(context).textTheme.bodySmall),
            ],
            const Spacer(),
            Expanded(
              flex: 4,
              child: Container(
                decoration: BoxDecoration(
                  color: AppColors.bg950.withValues(alpha: 0.4),
                  borderRadius: AppRadius.lg,
                  border: Border.all(color: AppColors.borderSoft),
                ),
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md,
                  vertical: AppSpacing.lg,
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: List.generate(bars.length, (index) {
                    final barHeight = math.max(18.0, bars[index] * 96);
                    final highlighted = index == 6 || index == 10;
                    return Expanded(
                      child: Align(
                        alignment: Alignment.bottomCenter,
                        child: Container(
                          margin: const EdgeInsets.symmetric(horizontal: 3),
                          height: barHeight,
                          decoration: BoxDecoration(
                            borderRadius: AppRadius.pill,
                            gradient: LinearGradient(
                              begin: Alignment.bottomCenter,
                              end: Alignment.topCenter,
                              colors: highlighted
                                  ? const [
                                      AppColors.accentCyan,
                                      AppColors.primary400,
                                    ]
                                  : [
                                      AppColors.primary500.withValues(
                                        alpha: 0.5,
                                      ),
                                      AppColors.accentViolet.withValues(
                                        alpha: 0.7,
                                      ),
                                    ],
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            const Wrap(
              spacing: AppSpacing.xs,
              runSpacing: AppSpacing.xs,
              children: [
                VFChip(label: 'Vista previa', tone: VFChipTone.neutral),
                VFChip(
                  label: 'Lista para reproducir',
                  tone: VFChipTone.success,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
