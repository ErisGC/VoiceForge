import 'package:flutter/foundation.dart';

/// Platform detection helpers that work correctly across Web, Android, and iOS.
///
/// On Flutter Web, [defaultTargetPlatform] returns the *simulated* platform
/// rather than the actual host.  Use [PlatformUtils.isWeb] to check for Web
/// first, then fall back to the target-platform checks for native.
class PlatformUtils {
  PlatformUtils._();

  /// `true` when running inside a browser (Flutter Web).
  static bool get isWeb => kIsWeb;

  /// `true` on native Android (not Web).
  static bool get isAndroid =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

  /// `true` on native iOS (not Web).
  static bool get isIOS =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.iOS;

  /// `true` on native macOS (not Web).
  static bool get isMacOS =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.macOS;

  /// `true` on native Windows (not Web).
  static bool get isWindows =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.windows;

  /// `true` on native Linux (not Web).
  static bool get isLinux =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.linux;

  /// `true` on any mobile platform (Android or iOS), but not Web.
  static bool get isMobile => isAndroid || isIOS;

  /// `true` on any desktop platform (macOS, Windows, Linux), but not Web.
  static bool get isDesktop => isMacOS || isWindows || isLinux;

  /// Returns a human-readable platform name for diagnostic purposes.
  static String get platformName {
    if (kIsWeb) return 'web';
    return switch (defaultTargetPlatform) {
      TargetPlatform.android => 'android',
      TargetPlatform.iOS => 'ios',
      TargetPlatform.macOS => 'macos',
      TargetPlatform.windows => 'windows',
      TargetPlatform.linux => 'linux',
      TargetPlatform.fuchsia => 'fuchsia',
    };
  }
}
