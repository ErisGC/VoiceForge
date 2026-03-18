import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_gradients.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_shadows.dart';
import '../../app/design_system/app_spacing.dart';
import '../../app/design_system/app_typography.dart';

enum VFButtonVariant { primary, secondary, ghost, destructive }

enum VFButtonSize { sm, md, lg }

class VFButton extends StatefulWidget {
  const VFButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = VFButtonVariant.primary,
    this.size = VFButtonSize.md,
    this.leadingIcon,
    this.trailingIcon,
    this.expand = false,
    this.isLoading = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final VFButtonVariant variant;
  final VFButtonSize size;
  final IconData? leadingIcon;
  final IconData? trailingIcon;
  final bool expand;
  final bool isLoading;

  @override
  State<VFButton> createState() => _VFButtonState();
}

class _VFButtonState extends State<VFButton> {
  bool _hovered = false;
  bool _focused = false;
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onPressed != null && !widget.isLoading;
    final metrics = _metricsFor(widget.size);
    final style = _styleFor(widget.variant, enabled: enabled);

    final button = AnimatedScale(
      duration: const Duration(milliseconds: 120),
      scale: _pressed ? 0.985 : 1,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOutCubic,
        width: widget.expand ? double.infinity : null,
        decoration: BoxDecoration(
          color: style.backgroundColor,
          gradient: style.gradient,
          borderRadius: AppRadius.pill,
          border: Border.all(
            color: _focused || _hovered
                ? style.hoverBorderColor
                : style.borderColor,
          ),
          boxShadow: style.shadow,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: widget.onPressed,
            borderRadius: AppRadius.pill,
            onHighlightChanged: enabled
                ? (value) => setState(() => _pressed = value)
                : null,
            onHover: enabled
                ? (value) => setState(() => _hovered = value)
                : null,
            splashColor: style.foregroundColor.withValues(alpha: 0.08),
            highlightColor: style.foregroundColor.withValues(alpha: 0.04),
            hoverColor: style.foregroundColor.withValues(alpha: 0.03),
            child: AnimatedOpacity(
              duration: const Duration(milliseconds: 120),
              opacity: enabled ? 1 : 0.45,
              child: Padding(
                padding: EdgeInsets.symmetric(
                  horizontal: metrics.horizontal,
                  vertical: metrics.vertical,
                ),
                child: Row(
                  mainAxisSize: widget.expand
                      ? MainAxisSize.max
                      : MainAxisSize.min,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (widget.isLoading) ...[
                      SizedBox(
                        width: metrics.iconSize,
                        height: metrics.iconSize,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: style.foregroundColor,
                        ),
                      ),
                    ] else ...[
                      if (widget.leadingIcon != null) ...[
                        Icon(
                          widget.leadingIcon,
                          size: metrics.iconSize,
                          color: style.foregroundColor,
                        ),
                        const SizedBox(width: AppSpacing.xs),
                      ],
                      Flexible(
                        child: Text(
                          widget.label,
                          overflow: TextOverflow.ellipsis,
                          style: metrics.textStyle.copyWith(
                            color: style.foregroundColor,
                          ),
                        ),
                      ),
                      if (widget.trailingIcon != null) ...[
                        const SizedBox(width: AppSpacing.xs),
                        Icon(
                          widget.trailingIcon,
                          size: metrics.iconSize,
                          color: style.foregroundColor,
                        ),
                      ],
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );

    return FocusableActionDetector(
      onShowFocusHighlight: (value) => setState(() => _focused = value),
      child: MouseRegion(
        onEnter: (_) => enabled ? setState(() => _hovered = true) : null,
        onExit: (_) => enabled ? setState(() => _hovered = false) : null,
        child: button,
      ),
    );
  }

  _ButtonMetrics _metricsFor(VFButtonSize size) {
    return switch (size) {
      VFButtonSize.sm => _ButtonMetrics(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
        iconSize: 16,
        textStyle: AppTypography.labelMedium,
      ),
      VFButtonSize.md => _ButtonMetrics(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.md,
        iconSize: 18,
        textStyle: AppTypography.labelLarge,
      ),
      VFButtonSize.lg => _ButtonMetrics(
        horizontal: AppSpacing.xl,
        vertical: AppSpacing.lg,
        iconSize: 20,
        textStyle: AppTypography.labelLarge.copyWith(fontSize: 16),
      ),
    };
  }

  _ButtonStyle _styleFor(VFButtonVariant variant, {required bool enabled}) {
    return switch (variant) {
      VFButtonVariant.primary => _ButtonStyle(
        backgroundColor: AppColors.primary500,
        borderColor: AppColors.primary500,
        hoverBorderColor: AppColors.primary400,
        foregroundColor: AppColors.text100,
        gradient: AppGradients.premium,
        shadow: [...AppShadows.glowPrimary, ...AppShadows.panel],
      ),
      VFButtonVariant.secondary => _ButtonStyle(
        backgroundColor: AppColors.surface800,
        borderColor: AppColors.borderStrong,
        hoverBorderColor: AppColors.primary400,
        foregroundColor: AppColors.text100,
        shadow: AppShadows.panel,
      ),
      VFButtonVariant.ghost => _ButtonStyle(
        backgroundColor: Colors.transparent,
        borderColor: Colors.transparent,
        hoverBorderColor: AppColors.borderSoft,
        foregroundColor: AppColors.text300,
        shadow: const [],
      ),
      VFButtonVariant.destructive => _ButtonStyle(
        backgroundColor: const Color(0x1FFF6B7A),
        borderColor: AppColors.danger500.withValues(alpha: 0.45),
        hoverBorderColor: AppColors.danger500,
        foregroundColor: AppColors.text100,
        shadow: const [
          BoxShadow(
            color: Color(0x22FF6B7A),
            blurRadius: 22,
            offset: Offset(0, 10),
          ),
        ],
      ),
    };
  }
}

class _ButtonStyle {
  const _ButtonStyle({
    required this.backgroundColor,
    required this.borderColor,
    required this.hoverBorderColor,
    required this.foregroundColor,
    this.gradient,
    required this.shadow,
  });

  final Color backgroundColor;
  final Color borderColor;
  final Color hoverBorderColor;
  final Color foregroundColor;
  final Gradient? gradient;
  final List<BoxShadow> shadow;
}

class _ButtonMetrics {
  const _ButtonMetrics({
    required this.horizontal,
    required this.vertical,
    required this.iconSize,
    required this.textStyle,
  });

  final double horizontal;
  final double vertical;
  final double iconSize;
  final TextStyle textStyle;
}
