import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/design_system/app_colors.dart';
import '../../app/design_system/app_gradients.dart';
import '../../app/design_system/app_radius.dart';
import '../../app/design_system/app_spacing.dart';
import '../../core/voiceforge_scope.dart';
import '../../core/widgets/vf_button.dart';
import '../../core/widgets/vf_card.dart';
import '../../core/widgets/vf_chip.dart';
import '../../core/widgets/vf_input.dart';
import '../../core/widgets/vf_panel.dart';
import '../../core/widgets/vf_section_header.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    if (email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = 'Completa correo y contraseña.');
      return;
    }

    final session = VoiceForgeScope.read(context).notifier!;
    setState(() => _errorMessage = null);
    try {
      await session.login(email: email, password: password);
      if (!mounted) {
        return;
      }
      context.go('/');
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() => _errorMessage = session.errorMessage);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = VoiceForgeScope.of(context).notifier!;
    return _AuthLayout(
      eyebrow: 'VoiceForge',
      title: 'Convierte voces con una experiencia sobria, precisa y lista para producción.',
      subtitle:
          'Accede a tus perfiles guardados, crea nuevas conversiones y mantén tus resultados organizados entre Android y Web.',
      formHeader: const VFSectionHeader(
        title: 'Acceso',
        subtitle:
            'Inicia sesión para conectar la biblioteca de voces, las muestras y el historial con el backend real.',
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          VFInput(
            label: 'Correo electrónico',
            hintText: 'tu@equipo.com',
            prefixIcon: Icons.alternate_email_rounded,
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
          ),
          const SizedBox(height: AppSpacing.md),
          VFInput(
            label: 'Contraseña',
            obscureText: true,
            prefixIcon: Icons.lock_outline_rounded,
            controller: _passwordController,
          ),
          if (_errorMessage != null) ...[
            const SizedBox(height: AppSpacing.md),
            Text(
              _errorMessage!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.danger500,
                  ),
            ),
          ],
          const SizedBox(height: AppSpacing.xl),
          VFButton(
            label: 'Entrar a VoiceForge',
            size: VFButtonSize.lg,
            expand: true,
            leadingIcon: Icons.arrow_forward_rounded,
            onPressed: _submit,
            isLoading: session.isBusy,
          ),
          const SizedBox(height: AppSpacing.md),
          VFButton(
            label: 'Crear cuenta',
            size: VFButtonSize.lg,
            expand: true,
            variant: VFButtonVariant.secondary,
            onPressed: () => context.go('/register'),
          ),
        ],
      ),
    );
  }
}

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _displayNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _consentConfirmed = true;
  String? _errorMessage;

  @override
  void dispose() {
    _displayNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final displayName = _displayNameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (displayName.isEmpty || email.isEmpty || password.isEmpty) {
      setState(() => _errorMessage = 'Completa nombre, correo y contraseña.');
      return;
    }
    if (!_consentConfirmed) {
      setState(() => _errorMessage = 'Debes confirmar el consentimiento para continuar.');
      return;
    }

    final session = VoiceForgeScope.read(context).notifier!;
    setState(() => _errorMessage = null);
    try {
      await session.register(
        displayName: displayName,
        email: email,
        password: password,
      );
      if (!mounted) {
        return;
      }
      context.go('/');
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() => _errorMessage = session.errorMessage);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = VoiceForgeScope.of(context).notifier!;
    return _AuthLayout(
      eyebrow: 'Registro',
      title: 'Crea tu espacio para voces guardadas, muestras y resultados.',
      subtitle:
          'El flujo arranca con consentimiento claro y una base preparada para seguir creciendo sin perder orden ni trazabilidad.',
      formHeader: const VFSectionHeader(
        title: 'Crear cuenta',
        subtitle:
            'Tu espacio queda listo para conectar voces, muestras y conversiones con la API real.',
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          VFInput(
            label: 'Nombre del equipo',
            hintText: 'VoiceForge Studio',
            prefixIcon: Icons.person_outline_rounded,
            controller: _displayNameController,
          ),
          const SizedBox(height: AppSpacing.md),
          VFInput(
            label: 'Correo electrónico',
            hintText: 'tu@equipo.com',
            prefixIcon: Icons.alternate_email_rounded,
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
          ),
          const SizedBox(height: AppSpacing.md),
          VFInput(
            label: 'Contraseña',
            obscureText: true,
            prefixIcon: Icons.lock_outline_rounded,
            controller: _passwordController,
          ),
          const SizedBox(height: AppSpacing.md),
          CheckboxListTile(
            value: _consentConfirmed,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            onChanged: (value) {
              setState(() => _consentConfirmed = value ?? false);
            },
            title: const Text(
              'Entiendo que toda clonación o creación de voz requiere consentimiento explícito.',
            ),
          ),
          if (_errorMessage != null) ...[
            const SizedBox(height: AppSpacing.sm),
            Text(
              _errorMessage!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.danger500,
                  ),
            ),
          ],
          const SizedBox(height: AppSpacing.sm),
          VFButton(
            label: 'Crear espacio',
            size: VFButtonSize.lg,
            expand: true,
            leadingIcon: Icons.rocket_launch_outlined,
            onPressed: _submit,
            isLoading: session.isBusy,
          ),
          const SizedBox(height: AppSpacing.md),
          VFButton(
            label: 'Volver al acceso',
            size: VFButtonSize.lg,
            expand: true,
            variant: VFButtonVariant.ghost,
            onPressed: () => context.go('/login'),
          ),
        ],
      ),
    );
  }
}

class _AuthLayout extends StatelessWidget {
  const _AuthLayout({
    required this.eyebrow,
    required this.title,
    required this.subtitle,
    required this.formHeader,
    required this.child,
  });

  final String eyebrow;
  final String title;
  final String subtitle;
  final Widget formHeader;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.sizeOf(context).width >= 960;

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          color: AppColors.bg950,
          gradient: AppGradients.hero,
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: AppGradients.glow(
                      alignment: Alignment.topRight,
                      color: AppColors.primary500,
                      opacity: 0.18,
                    ),
                  ),
                ),
              ),
            ),
            Positioned(
              left: -120,
              bottom: -80,
              child: IgnorePointer(
                child: Container(
                  width: 320,
                  height: 320,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: AppGradients.glow(
                      alignment: Alignment.center,
                      color: AppColors.accentCyan,
                      opacity: 0.14,
                    ),
                  ),
                ),
              ),
            ),
            SafeArea(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return SingleChildScrollView(
                    padding: const EdgeInsets.all(AppSpacing.xl),
                    child: ConstrainedBox(
                      constraints: BoxConstraints(
                        minHeight: constraints.maxHeight - (AppSpacing.xl * 2),
                      ),
                      child: Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(
                            maxWidth: AppSpacing.authMaxWidth,
                          ),
                          child: isWide
                              ? Row(
                                  children: [
                                    Expanded(
                                      child: _HeroPanel(
                                        eyebrow: eyebrow,
                                        title: title,
                                        subtitle: subtitle,
                                      ),
                                    ),
                                    const SizedBox(width: AppSpacing.xl),
                                    Expanded(
                                      child: VFCard(
                                        variant: VFCardVariant.elevated,
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            formHeader,
                                            const SizedBox(height: AppSpacing.xl),
                                            child,
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                )
                              : Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    _HeroPanel(
                                      eyebrow: eyebrow,
                                      title: title,
                                      subtitle: subtitle,
                                    ),
                                    const SizedBox(height: AppSpacing.lg),
                                    VFCard(
                                      variant: VFCardVariant.elevated,
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          formHeader,
                                          const SizedBox(height: AppSpacing.xl),
                                          child,
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeroPanel extends StatelessWidget {
  const _HeroPanel({
    required this.eyebrow,
    required this.title,
    required this.subtitle,
  });

  final String eyebrow;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return VFPanel(
      variant: VFPanelVariant.hero,
      padding: const EdgeInsets.all(AppSpacing.xxl),
      gradient: AppGradients.premium,
      borderRadius: AppRadius.xl,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          VFChip(
            label: eyebrow,
            icon: Icons.auto_awesome_rounded,
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(
            title,
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
                  color: AppColors.text100,
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: AppColors.text100.withValues(alpha: 0.84),
                  height: 1.5,
                ),
          ),
          const SizedBox(height: AppSpacing.xxl),
          const VFSectionHeader(
            title: 'Todo en un solo frente',
            subtitle:
                'Perfiles, muestras y resultados conviven en una misma identidad visual, con foco claro en la siguiente acción.',
          ),
          const SizedBox(height: AppSpacing.lg),
          Wrap(
            spacing: AppSpacing.sm,
            runSpacing: AppSpacing.sm,
            children: const [
              _HeroChip(text: 'Android + Web'),
              _HeroChip(text: 'API real'),
              _HeroChip(text: 'Resultados descargables'),
              _HeroChip(text: 'Consentimiento claro'),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroChip extends StatelessWidget {
  const _HeroChip({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return VFChip(
      label: text,
      icon: Icons.check_circle_outline,
    );
  }
}
