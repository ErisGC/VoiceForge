import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

class AppTypography {
  static TextTheme textTheme(TextTheme base) {
    final inter = GoogleFonts.interTextTheme(base);
    return inter.copyWith(
      displayLarge: _style(46, 54, FontWeight.w700),
      displayMedium: _style(40, 48, FontWeight.w700),
      displaySmall: _style(32, 40, FontWeight.w700),
      headlineLarge: _style(30, 38, FontWeight.w700),
      headlineMedium: _style(26, 34, FontWeight.w700),
      headlineSmall: _style(22, 30, FontWeight.w700),
      titleLarge: _style(18, 26, FontWeight.w600),
      titleMedium: _style(16, 24, FontWeight.w600),
      titleSmall: _style(14, 20, FontWeight.w600),
      bodyLarge: _style(16, 24, FontWeight.w400),
      bodyMedium: _style(14, 22, FontWeight.w400, color: AppColors.text300),
      bodySmall: _style(12, 18, FontWeight.w400, color: AppColors.text400),
      labelLarge: _style(15, 20, FontWeight.w600),
      labelMedium: _style(13, 18, FontWeight.w600, color: AppColors.text300),
      labelSmall: _style(11, 16, FontWeight.w600, color: AppColors.text400),
    );
  }

  static TextStyle get display => _style(46, 54, FontWeight.w700);
  static TextStyle get h1 => _style(30, 38, FontWeight.w700);
  static TextStyle get h2 => _style(26, 34, FontWeight.w700);
  static TextStyle get h3 => _style(22, 30, FontWeight.w700);
  static TextStyle get h4 => _style(18, 26, FontWeight.w600);
  static TextStyle get bodyLarge => _style(16, 24, FontWeight.w400);
  static TextStyle get bodyMedium =>
      _style(14, 22, FontWeight.w400, color: AppColors.text300);
  static TextStyle get bodySmall =>
      _style(12, 18, FontWeight.w400, color: AppColors.text400);
  static TextStyle get labelLarge => _style(15, 20, FontWeight.w600);
  static TextStyle get labelMedium =>
      _style(13, 18, FontWeight.w600, color: AppColors.text300);
  static TextStyle get labelSmall =>
      _style(11, 16, FontWeight.w600, color: AppColors.text400);
  static TextStyle get caption =>
      _style(11, 16, FontWeight.w500, color: AppColors.text500);

  static TextStyle _style(
    double size,
    double height,
    FontWeight weight, {
    Color color = AppColors.text100,
    double letterSpacing = 0,
  }) {
    return GoogleFonts.inter(
      fontSize: size,
      height: height / size,
      fontWeight: weight,
      color: color,
      letterSpacing: letterSpacing,
    );
  }
}
