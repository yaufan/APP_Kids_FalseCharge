import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:sharp_eyes/app/version.dart';

/// The version is written in three places; they have to agree.
void main() {
  test('pubspec, version.dart and the top of CHANGELOG.md agree', () {
    final pubspec = RegExp(r'^version:\s*([0-9.]+)\+', multiLine: true).firstMatch(File('pubspec.yaml').readAsStringSync())!.group(1);
    final changelog = RegExp(r'^## ([0-9.]+)', multiLine: true).firstMatch(File('../CHANGELOG.md').readAsStringSync())!.group(1);
    expect(appVersion, pubspec);
    expect(changelog, pubspec);
  });
}
