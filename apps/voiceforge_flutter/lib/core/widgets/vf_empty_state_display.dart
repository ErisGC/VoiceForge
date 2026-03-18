import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_spacing.dart';
import '../../app/design_system/app_typography.dart';
import 'vf_button.dart';
import 'vf_panel.dart';

/// An empty-state placeholder with icon, title, subtitle, and optional action.
///
/// This is the richer counterpart of [VFEmptyState] -- it supports a secondary
/// description and more prominent typography.
class VFEmptyStateDisplay extends StatelessWidget {
  const VFEmptyStateDisplay({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.description,
    this.actionLabel,
    this.onAction,
    this.actionIcon,
  });

  /// Large icon rendered at the top.
  final IconData icon;

  /// Main heading.
  final String title;

  /// Short subtitle beneath the heading.
  final String? subtitle;

  /// Optional longer description beneath the subtitle.
  final String? description;

  /// Label for the CTA button.
  final String? actionLabel;

  /// Called when the CTA button is tapped. If null, no button is shown.
  final VoidCallback? onAction;

  /// Leading icon for the CTA button.
  final IconData? actionIcon;

  @override
  Widget build(BuildContext context) {
    return VFPanel(
      variant: VFPanelVariant.subdued,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: AppColors.primary500.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 32, color: AppColors.primary500),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(
            title,
            textAlign: TextAlign.center,
            style: AppTypography.h4,
          ),
          if (subtitle != null) ...[
            const SizedBox(height: AppSpacing.xs),
            Text(
              subtitle!,
              textAlign: TextAlign.center,
              style: AppTypography.bodyMedium,
            ),
          ],
          if (description != null) ...[
            const SizedBox(height: AppSpacing.sm),
            Text(
              description!,
              textAlign: TextAlign.center,
              style: AppTypography.bodySmall,
            ),
          ],
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: AppSpacing.xl),
            VFButton(
              label: actionLabel!,
              onPressed: onAction,
              leadingIcon: actionIcon,
            ),
          ],
        ],
      ),
    );
  }
}
