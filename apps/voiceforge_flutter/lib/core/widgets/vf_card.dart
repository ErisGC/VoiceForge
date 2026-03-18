import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_shadows.dart';
import '../../app/design_system/app_spacing.dart';

enum VFCardVariant { base, interactive, elevated }

class VFCard extends StatefulWidget {
  const VFCard({
    super.key,
    required this.child,
    this.variant = VFCardVariant.base,
    this.padding = AppSpacing.panelPadding,
    this.onTap,
  });

  final Widget child;
  final VFCardVariant variant;
  final EdgeInsets padding;
  final VoidCallback? onTap;

  @override
  State<VFCard> createState() => _VFCardState();
}

class _VFCardState extends State<VFCard> {
  bool _hovered = false;
  bool _focused = false;
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final interactive =
        widget.variant == VFCardVariant.interactive || widget.onTap != null;
    final baseColor = widget.variant == VFCardVariant.elevated
        ? AppColors.surface700
        : AppColors.surface800;
    final translateY = interactive && _hovered ? -3.0 : 0.0;
    final scale = _pressed ? 0.995 : 1.0;

    final decoration = BoxDecoration(
      color: baseColor,
      borderRadius: AppRadius.xl,
      border: Border.all(
        color: _focused || _hovered
            ? AppColors.borderStrong
            : AppColors.borderSoft,
      ),
      boxShadow: widget.variant == VFCardVariant.elevated || _hovered
          ? [...AppShadows.panel, ...AppShadows.glowPrimary]
          : AppShadows.panel,
    );

    final card = AnimatedScale(
      duration: const Duration(milliseconds: 140),
      scale: scale,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOutCubic,
        transform: Matrix4.translationValues(0, translateY, 0),
        decoration: decoration,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: widget.onTap,
            borderRadius: AppRadius.xl,
            onHighlightChanged: (value) => setState(() => _pressed = value),
            onHover: interactive
                ? (value) => setState(() => _hovered = value)
                : null,
            focusColor: AppColors.primary500.withValues(alpha: 0.08),
            hoverColor: AppColors.primary500.withValues(alpha: 0.04),
            splashColor: AppColors.primary500.withValues(alpha: 0.08),
            highlightColor: AppColors.primary500.withValues(alpha: 0.05),
            child: Padding(padding: widget.padding, child: widget.child),
          ),
        ),
      ),
    );

    if (!interactive) {
      return card;
    }

    return FocusableActionDetector(
      onShowFocusHighlight: (value) => setState(() => _focused = value),
      child: MouseRegion(
        onEnter: (_) => setState(() => _hovered = true),
        onExit: (_) => setState(() => _hovered = false),
        child: card,
      ),
    );
  }
}
