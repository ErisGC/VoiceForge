import 'package:flutter/material.dart';

import 'app_colors.dart';

class AppGradients {
  static const LinearGradient hero = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF11182E), Color(0xFF172142), Color(0xFF0F1834)],
  );

  static const LinearGradient premium = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF6375FF), Color(0xFF7A79FF), Color(0xFF4FD1FF)],
  );

  static RadialGradient glow({
    Alignment alignment = Alignment.topRight,
    Color color = AppColors.primary500,
    double opacity = 0.2,
  }) {
    return RadialGradient(
      center: alignment,
      radius: 1.2,
      colors: [
        color.withValues(alpha: opacity),
        color.withValues(alpha: 0),
      ],
      stops: const [0, 1],
    );
  }
}
