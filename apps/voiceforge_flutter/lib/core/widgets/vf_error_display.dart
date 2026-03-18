import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_spacing.dart';
import 'vf_button.dart';
import 'vf_panel.dart';

/// Displays an error message with an optional retry button.
///
/// Follows the VF design system: uses [VFPanel] as the container and
/// [VFButton] for the retry action.  All UI text is in Spanish.
class VFErrorDisplay extends StatelessWidget {
  const VFErrorDisplay({
    super.key,
    required this.message,
    this.onRetry,
    this.icon = Icons.error_outline_rounded,
    this.retryLabel = 'Reintentar',
  });

  /// The error message to display.
  final String message;

  /// Called when the user taps the retry button. If null, no button is shown.
  final VoidCallback? onRetry;

  /// Icon shown above the message.
  final IconData icon;

  /// Label for the retry button.
  final String retryLabel;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return VFPanel(
      variant: VFPanelVariant.subdued,
      borderColor: AppColors.danger500.withValues(alpha: 0.35),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 40, color: AppColors.danger500),
          const SizedBox(height: AppSpacing.lg),
          Text(
            message,
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: AppColors.text300,
            ),
          ),
          if (onRetry != null) ...[
            const SizedBox(height: AppSpacing.xl),
            VFButton(
              label: retryLabel,
              onPressed: onRetry,
              variant: VFButtonVariant.secondary,
              leadingIcon: Icons.refresh_rounded,
            ),
          ],
        ],
      ),
    );
  }
}
