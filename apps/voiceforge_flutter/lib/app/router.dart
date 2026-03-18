import 'package:go_router/go_router.dart';

import '../core/widgets/voiceforge_shell.dart';
import '../features/auth/auth_screens.dart';
import '../features/conversions/conversion_screens.dart';
import '../features/dashboard/dashboard_screen.dart';
import '../features/voices/voice_screens.dart';

final GoRouter router = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: LoginScreen()),
    ),
    GoRoute(
      path: '/register',
      pageBuilder: (context, state) =>
          const NoTransitionPage(child: RegisterScreen()),
    ),
    ShellRoute(
      builder: (context, state, child) {
        return VoiceForgeShell(currentLocation: state.uri.path, child: child);
      },
      routes: [
        GoRoute(
          path: '/',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: DashboardScreen()),
        ),
        GoRoute(
          path: '/voices',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: VoiceLibraryScreen()),
        ),
        GoRoute(
          path: '/voices/:voiceId',
          pageBuilder: (context, state) => NoTransitionPage(
            child: VoiceProfileDetailScreen(
              voiceId: state.pathParameters['voiceId']!,
            ),
          ),
        ),
        GoRoute(
          path: '/voices/:voiceId/upload',
          pageBuilder: (context, state) => NoTransitionPage(
            child: UploadSamplesScreen(
              voiceId: state.pathParameters['voiceId']!,
            ),
          ),
        ),
        GoRoute(
          path: '/voices/:voiceId/record',
          pageBuilder: (context, state) => NoTransitionPage(
            child: RecordSampleScreen(
              voiceId: state.pathParameters['voiceId']!,
            ),
          ),
        ),
        GoRoute(
          path: '/conversions/create',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: CreateConversionScreen()),
        ),
        GoRoute(
          path: '/conversions/history',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: ConversionHistoryScreen()),
        ),
        GoRoute(
          path: '/conversions/history/:jobId',
          pageBuilder: (context, state) => NoTransitionPage(
            child: ResultPlayerScreen(jobId: state.pathParameters['jobId']!),
          ),
        ),
      ],
    ),
  ],
);
