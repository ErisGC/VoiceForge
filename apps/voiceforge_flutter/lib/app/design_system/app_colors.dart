import 'package:flutter/material.dart';

class AppColors {
  static const Color bg950 = Color(0xFF0B1020);
  static const Color bg900 = Color(0xFF12182B);
  static const Color surface800 = Color(0xFF182038);
  static const Color surface700 = Color(0xFF212B47);

  static const Color text100 = Color(0xFFF3F6FF);
  static const Color text300 = Color(0xFFB9C3E1);
  static const Color text400 = Color(0xFF8C97B8);
  static const Color text500 = Color(0xFF697394);

  static const Color primary500 = Color(0xFF6D7CFF);
  static const Color primary400 = Color(0xFF8592FF);
  static const Color primary600 = Color(0xFF5869F0);
  static const Color accentCyan = Color(0xFF4FD1FF);
  static const Color accentViolet = Color(0xFF9E7BFF);

  static const Color success500 = Color(0xFF3DDC97);
  static const Color warning500 = Color(0xFFFFB84D);
  static const Color danger500 = Color(0xFFFF6B7A);
  static const Color info500 = Color(0xFF59A8FF);

  static const Color borderSoft = Color(0x24AABDFF);
  static const Color borderStrong = Color(0x3DAABDFF);

  static const Color shadowDark = Color(0x8C030814);
  static const Color shadowSoft = Color(0x4D030814);
  static const Color black = Color(0xFF000000);
  static const Color white = Color(0xFFFFFFFF);

  static ColorScheme get colorScheme {
    return ColorScheme.fromSeed(
      seedColor: primary500,
      brightness: Brightness.dark,
    ).copyWith(
      primary: primary500,
      onPrimary: text100,
      primaryContainer: primary600,
      onPrimaryContainer: text100,
      secondary: accentCyan,
      onSecondary: bg950,
      secondaryContainer: surface700,
      onSecondaryContainer: text100,
      tertiary: accentViolet,
      onTertiary: text100,
      tertiaryContainer: surface700,
      onTertiaryContainer: text100,
      surface: surface800,
      onSurface: text100,
      surfaceContainerHighest: surface700,
      onSurfaceVariant: text300,
      outline: borderSoft,
      outlineVariant: borderStrong,
      error: danger500,
      onError: text100,
      errorContainer: const Color(0x33FF6B7A),
      onErrorContainer: text100,
      shadow: shadowDark,
      scrim: const Color(0xCC030814),
      inverseSurface: text100,
      onInverseSurface: bg950,
      inversePrimary: primary400,
    );
  }
}
