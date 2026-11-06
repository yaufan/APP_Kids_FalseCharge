import 'package:flutter_tts/flutter_tts.dart';

/// Reads out what 小變 says and the names of things, for children who
/// cannot read yet: Taiwanese Mandarin, then (if a parent turned it on) the
/// English name ("氣球, balloon"). It uses the phone's own speech; parents
/// can turn it off.
abstract interface class Voice {
  /// Says [zh] in Mandarin, then [en] (if any) in English.
  Future<void> say(String zh, {String? en});
  Future<void> stop();
}

class SystemVoice implements Voice {
  FlutterTts? _tts;
  var _said = 0;

  Future<FlutterTts> _engine() async {
    final existing = _tts;
    if (existing != null) return existing;
    final tts = _tts = FlutterTts();
    await tts.awaitSpeakCompletion(true);
    await tts.setSpeechRate(0.45);
    await tts.setPitch(1.2);
    return tts;
  }

  @override
  Future<void> say(String zh, {String? en}) async {
    final turn = ++_said;
    try {
      final tts = await _engine();
      await tts.stop();
      if (zh.isNotEmpty) {
        await tts.setLanguage('zh-TW');
        await tts.speak(zh);
      }
      if (en == null || en.isEmpty || turn != _said) return;
      await tts.setLanguage('en-US');
      await tts.speak(en);
    } catch (_) {
      // No speech engine (tests, or a phone without one): the words on
      // screen and the pictures are enough.
    }
  }

  @override
  Future<void> stop() async {
    _said++;
    try {
      await _tts?.stop();
    } catch (_) {}
  }
}

class SilentVoice implements Voice {
  const SilentVoice();

  @override
  Future<void> say(String zh, {String? en}) async {}

  @override
  Future<void> stop() async {}
}

/// Remembers what was said (tests).
class RecordingVoice implements Voice {
  final said = <String>[];

  @override
  Future<void> say(String zh, {String? en}) async => said.add(en == null ? zh : '$zh|$en');

  @override
  Future<void> stop() async {}
}
