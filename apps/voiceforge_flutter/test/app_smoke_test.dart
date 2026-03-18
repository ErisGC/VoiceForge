import 'package:flutter_test/flutter_test.dart';
import 'package:voiceforge_flutter/app/voiceforge_app.dart';

void main() {
  testWidgets('renders login entrypoint', (tester) async {
    await tester.pumpWidget(const VoiceForgeApp());
    await tester.pumpAndSettle();

    expect(find.text('Entrar a VoiceForge'), findsOneWidget);
  });
}
