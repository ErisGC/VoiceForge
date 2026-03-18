import 'package:flutter/material.dart';

import 'app_colors.dart';

class AppShadows {
  static List<BoxShadow> panel = const [
    BoxShadow(
      color: AppColors.shadowSoft,
      blurRadius: 28,
      offset: Offset(0, 16),
    ),
  ];

  static List<BoxShadow> elevated = const [
    BoxShadow(
      color: AppColors.shadowDark,
      blurRadius: 40,
      offset: Offset(0, 20),
    ),
    BoxShadow(color: Color(0x14000000), blurRadius: 10, offset: Offset(0, 3)),
  ];

  static List<BoxShadow> glowPrimary = const [
    BoxShadow(
      color: Color(0x2A6D7CFF),
      blurRadius: 24,
      spreadRadius: -2,
      offset: Offset(0, 10),
    ),
  ];

  static List<BoxShadow> glowCyan = const [
    BoxShadow(
      color: Color(0x224FD1FF),
      blurRadius: 28,
      spreadRadius: -4,
      offset: Offset(0, 8),
    ),
  ];
}
