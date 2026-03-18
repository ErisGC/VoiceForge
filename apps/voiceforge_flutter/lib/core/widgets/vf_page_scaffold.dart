import 'package:flutter/material.dart';

import '../../app/design_system/app_spacing.dart';

class VFPageScaffold extends StatelessWidget {
  const VFPageScaffold({
    super.key,
    required this.children,
    this.maxWidth = AppSpacing.contentMaxWidth,
  });

  final List<Widget> children;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final padding = width >= 900
        ? AppSpacing.pagePaddingDesktop
        : AppSpacing.pagePaddingMobile;

    return LayoutBuilder(
      builder: (context, constraints) {
        return Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: BoxConstraints(maxWidth: maxWidth),
            child: ListView.separated(
              padding: padding,
              itemCount: children.length,
              separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.xl),
              itemBuilder: (context, index) => children[index],
            ),
          ),
        );
      },
    );
  }
}
