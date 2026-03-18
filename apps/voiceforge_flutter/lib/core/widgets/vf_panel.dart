import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_shadows.dart';
import '../../app/design_system/app_spacing.dart';

enum VFPanelVariant { base, elevated, subdued, hero }

class VFPanel extends StatelessWidget {
  const VFPanel({
    super.key,
    required this.child,
    this.padding = AppSpacing.panelPadding,
    this.variant = VFPanelVariant.base,
    this.borderColor,
    this.borderRadius = AppRadius.xl,
    this.gradient,
    this.width,
    this.height,
  });

  final Widget child;
  final EdgeInsets padding;
  final VFPanelVariant variant;
  final Color? borderColor;
  final BorderRadius borderRadius;
  final Gradient? gradient;
  final double? width;
  final double? height;

  @override
  Widget build(BuildContext context) {
    final backgroundColor = switch (variant) {
      VFPanelVariant.base => AppColors.surface800,
      VFPanelVariant.elevated => AppColors.surface700,
      VFPanelVariant.subdued => AppColors.bg900,
      VFPanelVariant.hero => AppColors.surface800,
    };

    final shadows = switch (variant) {
      VFPanelVariant.base => AppShadows.panel,
      VFPanelVariant.elevated => [
        ...AppShadows.elevated,
        ...AppShadows.glowPrimary,
      ],
      VFPanelVariant.subdued => const <BoxShadow>[],
      VFPanelVariant.hero => [...AppShadows.panel, ...AppShadows.glowCyan],
    };

    return Container(
      width: width,
      height: height,
      padding: padding,
      decoration: BoxDecoration(
        color: gradient == null ? backgroundColor : null,
        gradient: gradient,
        borderRadius: borderRadius,
        border: Border.all(color: borderColor ?? AppColors.borderSoft),
        boxShadow: shadows,
      ),
      child: child,
    );
  }
}
