import 'package:flutter_test/flutter_test.dart';

import 'package:voiceforge_flutter/app/voiceforge_app.dart';

void main() {
  testWidgets('VoiceForgeApp builds without errors', (WidgetTester tester) async {
    await tester.pumpWidget(const VoiceForgeApp());
    // The app should render and produce at least one widget.
    expect(find.byType(VoiceForgeApp), findsOneWidget);
  });
}
