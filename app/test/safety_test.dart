import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sharp_eyes/features/parent/parent_gate.dart';

import 'helpers.dart';

/// Privacy and the parent gate (docs/design.md: no network, nothing leaves
/// the phone, parent mode only through the gate).
void main() {
  test('the app asks for no permissions and takes no links from other apps', () {
    final manifest = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
    expect(manifest, isNot(contains('uses-permission')), reason: 'no internet, camera, location…');
    expect(manifest, contains('android:name="flutter_deeplinking_enabled" android:value="false"'));
    expect(File('ios/Runner/Info.plist').readAsStringSync(), contains('<key>FlutterDeepLinkingEnabled</key>\n\t<false/>'));
  });

  test('the phone\'s speech engine can be found on Android 11 and later', () {
    final manifest = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
    final queries = RegExp(r'<queries>[\s\S]*</queries>').stringMatch(manifest) ?? '';
    expect(queries, contains('android.intent.action.TTS_SERVICE'));
  });

  test('nothing is backed up or moved to another phone: the play stays only on this phone', () {
    final manifest = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
    expect(manifest, contains('android:allowBackup="false"'));
    expect(manifest, contains('android:fullBackupContent="false"'));
    expect(manifest, contains('android:dataExtractionRules="@xml/data_extraction_rules"'));
    final rules = File('android/app/src/main/res/xml/data_extraction_rules.xml').readAsStringSync();
    for (final part in ['cloud-backup', 'device-transfer']) {
      final block = RegExp('<$part>([\\s\\S]*?)</$part>').firstMatch(rules)?.group(1) ?? '';
      for (final domain in ['root', 'file', 'database', 'sharedpref', 'external']) {
        expect(block, contains('<exclude domain="$domain" />'), reason: '$part $domain');
      }
    }
  });

  test('the build checks the APK asks for no camera, microphone, contacts, photos or location', () {
    for (final f in ['app.yml', 'release.yml']) {
      final yml = File('../.github/workflows/$f').readAsStringSync();
      final banned = RegExp(r"grep -E '([^']*)' permissions\.txt").firstMatch(yml)?.group(1)?.split('|') ?? const [];
      for (final p in ['INTERNET', 'LOCATION', 'AD_ID', 'CAMERA', 'RECORD_AUDIO', 'READ_CONTACTS', 'READ_MEDIA_', 'READ_EXTERNAL_STORAGE']) {
        expect(banned, contains(p), reason: '$f $p');
      }
    }
  });

  testWidgets('parent mode and unknown pages cannot be opened without the gate', (tester) async {
    final app = await TestApp.start(tester);
    app.go('/parent');
    await app.settle();
    expect(app.location, '/', reason: 'no pass from the gate');
    ParentPass.grant();
    app.go('/parent');
    await app.settle();
    expect(app.location, '/parent', reason: 'right after the gate');
    app.go('/');
    await app.settle();
    app.go('/parent');
    await app.settle();
    expect(app.location, '/', reason: 'the pass is used up');
    for (final bad in ['/play/nowhere/odd', '/play/park/nothing', '/place/moon']) {
      app.go(bad);
      await app.settle();
      expect(app.location, '/', reason: bad);
    }
    app.go('/place/park');
    await app.settle(800);
    expect(app.location, '/place/park');
    await app.end();
  });
}
