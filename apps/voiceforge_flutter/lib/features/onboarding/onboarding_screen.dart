import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_gradients.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';
import '../../app/design_system/app_typography.dart';
import '../../core/widgets/vf_button.dart';

/// Key used in SharedPreferences to track whether onboarding has been completed.
const String kOnboardingCompleteKey = 'voiceforge_onboarding_complete';

/// Checks SharedPreferences to determine if the user has completed onboarding.
Future<bool> hasCompletedOnboarding() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getBool(kOnboardingCompleteKey) ?? false;
}

/// Marks onboarding as completed in SharedPreferences.
Future<void> markOnboardingComplete() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setBool(kOnboardingCompleteKey, true);
}

/// Three-page onboarding flow: Welcome, How it works, Create first profile.
///
/// Uses SharedPreferences to persist the onboarding-completed flag so the
/// screen is only shown once per device.
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _controller = PageController();
  int _currentPage = 0;

  static const _pages = <_OnboardingPageData>[
    _OnboardingPageData(
      icon: Icons.record_voice_over_rounded,
      title: 'Bienvenido a VoiceForge',
      body: 'Transforma cualquier audio para que suene como tu voz '
          'favorita, conservando el contenido hablado.',
    ),
    _OnboardingPageData(
      icon: Icons.auto_awesome_rounded,
      title: 'Como funciona',
      body: '1. Graba o sube muestras de voz.\n'
          '2. Crea un perfil de voz.\n'
          '3. Sube el audio que quieras convertir y listo.',
    ),
    _OnboardingPageData(
      icon: Icons.mic_rounded,
      title: 'Crea tu primer perfil',
      body: 'Empieza grabando unas muestras de tu voz. '
          'Solo toma un par de minutos.',
    ),
  ];

  void _next() {
    if (_currentPage < _pages.length - 1) {
      _controller.nextPage(
        duration: const Duration(milliseconds: 350),
        curve: Curves.easeOutCubic,
      );
    } else {
      _finish();
    }
  }

  void _skip() => _finish();

  Future<void> _finish() async {
    await markOnboardingComplete();
    if (mounted) context.go('/login');
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isLast = _currentPage == _pages.length - 1;

    return Scaffold(
      backgroundColor: AppColors.bg950,
      body: SafeArea(
        child: Column(
          children: [
            // Skip button
            Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: VFButton(
                  label: 'Saltar',
                  variant: VFButtonVariant.ghost,
                  size: VFButtonSize.sm,
                  onPressed: _skip,
                ),
              ),
            ),
            // Pages
            Expanded(
              child: PageView.builder(
                controller: _controller,
                onPageChanged: (index) => setState(() => _currentPage = index),
                itemCount: _pages.length,
                itemBuilder: (context, index) => _OnboardingPage(
                  data: _pages[index],
                ),
              ),
            ),
            // Dots
            Padding(
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.lg),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  _pages.length,
                  (i) => _Dot(active: i == _currentPage),
                ),
              ),
            ),
            // Action button
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.xl,
                0,
                AppSpacing.xl,
                AppSpacing.xxl,
              ),
              child: VFButton(
                label: isLast ? 'Comenzar' : 'Siguiente',
                onPressed: _next,
                expand: true,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OnboardingPageData {
  const _OnboardingPageData({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;
}

class _OnboardingPage extends StatelessWidget {
  const _OnboardingPage({required this.data});

  final _OnboardingPageData data;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xxl),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 100,
            height: 100,
            decoration: BoxDecoration(
              gradient: AppGradients.premium,
              borderRadius: AppRadius.xl,
            ),
            child: Icon(data.icon, size: 48, color: AppColors.text100),
          ),
          const SizedBox(height: AppSpacing.xxxl),
          Text(
            data.title,
            textAlign: TextAlign.center,
            style: AppTypography.h2,
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            data.body,
            textAlign: TextAlign.center,
            style: AppTypography.bodyMedium,
          ),
        ],
      ),
    );
  }
}

class _Dot extends StatelessWidget {
  const _Dot({required this.active});

  final bool active;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      margin: const EdgeInsets.symmetric(horizontal: 4),
      width: active ? 24 : 8,
      height: 8,
      decoration: BoxDecoration(
        color: active ? AppColors.primary500 : AppColors.text500,
        borderRadius: AppRadius.pill,
      ),
    );
  }
}
