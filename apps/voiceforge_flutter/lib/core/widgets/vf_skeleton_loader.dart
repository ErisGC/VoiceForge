import 'package:flutter/material.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';

/// A shimmer-effect skeleton loading placeholder.
///
/// Use [VFSkeletonLoader] to replace content areas while data is being fetched.
/// The shimmer animation sweeps a gradient highlight across the placeholder
/// from left to right in a loop.
///
/// ```dart
/// VFSkeletonLoader(width: 200, height: 16);                 // single bar
/// VFSkeletonLines(count: 3);                                  // multiple text lines
/// VFSkeletonLoader.card(height: 120);                        // card-sized block
/// ```
class VFSkeletonLoader extends StatefulWidget {
  const VFSkeletonLoader({
    super.key,
    this.width,
    this.height = 16,
    this.borderRadius = AppRadius.sm,
  });

  /// Creates a card-sized skeleton block.
  const VFSkeletonLoader.card({
    super.key,
    this.width,
    this.height = 120,
    this.borderRadius = AppRadius.xl,
  });

  /// Width of the skeleton. Defaults to fill available space.
  final double? width;

  /// Height of the skeleton.
  final double height;

  /// Border radius of the skeleton rectangle.
  final BorderRadius borderRadius;

  @override
  State<VFSkeletonLoader> createState() => _VFSkeletonLoaderState();
}

class _VFSkeletonLoaderState extends State<VFSkeletonLoader>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1400),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: widget.borderRadius,
            gradient: _shimmerGradient(_controller.value),
          ),
        );
      },
    );
  }
}

/// A stack of shimmer skeleton lines, typically used as a text placeholder.
class VFSkeletonLines extends StatefulWidget {
  const VFSkeletonLines({
    super.key,
    this.count = 3,
    this.lineHeight = 14,
    this.spacing = AppSpacing.xs,
  });

  /// Number of skeleton lines.
  final int count;

  /// Height of each line.
  final double lineHeight;

  /// Vertical spacing between lines.
  final double spacing;

  @override
  State<VFSkeletonLines> createState() => _VFSkeletonLinesState();
}

class _VFSkeletonLinesState extends State<VFSkeletonLines>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1400),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: List.generate(widget.count, (index) {
            final isLast = index == widget.count - 1;
            return Padding(
              padding: EdgeInsets.only(
                bottom: index < widget.count - 1 ? widget.spacing : 0,
              ),
              child: FractionallySizedBox(
                widthFactor: isLast ? 0.6 : 1.0,
                child: Container(
                  height: widget.lineHeight,
                  decoration: BoxDecoration(
                    borderRadius: AppRadius.sm,
                    gradient: _shimmerGradient(_controller.value),
                  ),
                ),
              ),
            );
          }),
        );
      },
    );
  }
}

LinearGradient _shimmerGradient(double value) {
  return LinearGradient(
    begin: Alignment(-1.0 + 2.0 * value, 0),
    end: Alignment(-1.0 + 2.0 * value + 1.0, 0),
    colors: const [
      AppColors.surface800,
      AppColors.surface700,
      AppColors.surface800,
    ],
    stops: const [0.0, 0.5, 1.0],
  );
}
