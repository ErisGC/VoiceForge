import 'package:flutter/material.dart';

import 'design_system/app_colors.dart';
import 'design_system/app_gradients.dart';
import 'design_system/app_radius.dart';
import 'design_system/app_shadows.dart';
import 'design_system/app_spacing.dart';
import 'design_system/app_typography.dart';

class AppTheme {
  static ThemeData build() {
    final colorScheme = AppColors.colorScheme;
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.bg950,
      canvasColor: AppColors.bg900,
      splashFactory: InkRipple.splashFactory,
    );

    final textTheme = AppTypography.textTheme(base.textTheme);

    return base.copyWith(
      textTheme: textTheme,
      primaryTextTheme: textTheme,
      scaffoldBackgroundColor: AppColors.bg950,
      dividerColor: AppColors.borderSoft,
      disabledColor: AppColors.text500,
      iconTheme: const IconThemeData(color: AppColors.text300),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.text100,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
      ),
      cardTheme: CardThemeData(
        color: AppColors.surface800,
        elevation: 0,
        margin: EdgeInsets.zero,
        shadowColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: AppRadius.lg,
          side: const BorderSide(color: AppColors.borderSoft),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface800,
        hintStyle: AppTypography.bodyMedium.copyWith(color: AppColors.text500),
        labelStyle: AppTypography.bodyMedium.copyWith(color: AppColors.text400),
        helperStyle: AppTypography.bodySmall,
        errorStyle: AppTypography.bodySmall.copyWith(
          color: AppColors.danger500,
        ),
        prefixIconColor: AppColors.text400,
        suffixIconColor: AppColors.text400,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        border: _inputBorder(AppColors.borderSoft),
        enabledBorder: _inputBorder(AppColors.borderSoft),
        disabledBorder: _inputBorder(AppColors.borderSoft),
        focusedBorder: _inputBorder(AppColors.primary400, width: 1.4),
        errorBorder: _inputBorder(AppColors.danger500),
        focusedErrorBorder: _inputBorder(AppColors.danger500, width: 1.4),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: AppColors.bg900.withValues(alpha: 0.96),
        surfaceTintColor: Colors.transparent,
        shadowColor: Colors.transparent,
        elevation: 0,
        indicatorColor: AppColors.primary500.withValues(alpha: 0.16),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return AppTypography.labelSmall.copyWith(
            color: selected ? AppColors.text100 : AppColors.text400,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(
            color: selected ? AppColors.primary400 : AppColors.text400,
            size: 22,
          );
        }),
      ),
      chipTheme: base.chipTheme.copyWith(
        backgroundColor: AppColors.surface700,
        selectedColor: AppColors.primary500.withValues(alpha: 0.18),
        disabledColor: AppColors.surface700.withValues(alpha: 0.72),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        shape: RoundedRectangleBorder(
          borderRadius: AppRadius.pill,
          side: const BorderSide(color: AppColors.borderSoft),
        ),
        side: const BorderSide(color: AppColors.borderSoft),
        labelStyle: AppTypography.labelSmall.copyWith(color: AppColors.text300),
      ),
      textSelectionTheme: TextSelectionThemeData(
        cursorColor: AppColors.primary400,
        selectionColor: AppColors.primary500.withValues(alpha: 0.28),
        selectionHandleColor: AppColors.primary400,
      ),
      checkboxTheme: CheckboxThemeData(
        shape: RoundedRectangleBorder(borderRadius: AppRadius.sm),
        side: const BorderSide(color: AppColors.borderStrong),
        fillColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return AppColors.primary500;
          }
          return Colors.transparent;
        }),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.text100,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          side: const BorderSide(color: AppColors.borderStrong),
          shape: RoundedRectangleBorder(borderRadius: AppRadius.md),
          textStyle: AppTypography.labelLarge,
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          foregroundColor: AppColors.text100,
          backgroundColor: AppColors.primary500,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          textStyle: AppTypography.labelLarge,
          shape: RoundedRectangleBorder(borderRadius: AppRadius.md),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          foregroundColor: AppColors.text100,
          backgroundColor: AppColors.primary500,
          elevation: 0,
          shadowColor: Colors.transparent,
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: AppRadius.md),
          textStyle: AppTypography.labelLarge,
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.text300,
          textStyle: AppTypography.labelLarge,
          shape: RoundedRectangleBorder(borderRadius: AppRadius.md),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.surface700,
        contentTextStyle: AppTypography.bodyMedium.copyWith(
          color: AppColors.text100,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: AppRadius.md,
          side: const BorderSide(color: AppColors.borderSoft),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.surface800,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: AppRadius.xl),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: AppColors.surface800,
        surfaceTintColor: Colors.transparent,
      ),
      extensions: const <ThemeExtension<dynamic>>[],
    );
  }

  static OutlineInputBorder _inputBorder(Color color, {double width = 1}) {
    return OutlineInputBorder(
      borderRadius: AppRadius.md,
      borderSide: BorderSide(color: color, width: width),
    );
  }

  static BoxDecoration shellBackgroundDecoration() {
    return BoxDecoration(
      color: AppColors.bg950,
      gradient: AppGradients.hero,
      boxShadow: AppShadows.panel,
    );
  }
}

ThemeData buildVoiceForgeTheme() => AppTheme.build();
