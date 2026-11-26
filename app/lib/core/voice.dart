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
  Future<FlutterTts>? _setUp;
  String? _language;

  /// Counts the lines asked for (and the stops): only the newest is said.
  var _turn = 0;

  /// The engine, set up once. Every line waits for the whole set-up, so a
  /// line asked for while the first one (the welcome) is still setting up
  /// is not cut off by the first one's late stop(): the newer line is the
  /// one that is said, and nothing is said after stop().
  Future<FlutterTts> _engine() => _setUp ??= () async {
        final tts = _tts = FlutterTts();
        await tts.awaitSpeakCompletion(true);
        await tts.setSpeechRate(0.45);
        await tts.setPitch(1.2);
        return tts;
      }();

  Future<void> _speakIn(FlutterTts tts, String language, String text) async {
    if (language != _language) {
      _language = language;
      await tts.setLanguage(language);
    }
    await tts.speak(text);
  }

  @override
  Future<void> say(String zh, {String? en}) async {
    final turn = ++_turn;
    try {
      final tts = await _engine();
      if (turn != _turn) return;
      await tts.stop();
      // A newer line, or a stop, while this one waited.
      if (turn != _turn) return;
      if (zh.isNotEmpty) await _speakIn(tts, 'zh-TW', zh);
      if (en == null || en.isEmpty || turn != _turn) return;
      await _speakIn(tts, 'en-US', en);
    } catch (_) {
      // No speech engine (tests, or a phone without one): the words on
      // screen and the pictures are enough.
    }
  }

  @override
  Future<void> stop() async {
    _turn++;
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

/// Remembers what was said, and how often it was stopped (tests).
class RecordingVoice implements Voice {
  final said = <String>[];
  var stops = 0;

  @override
  Future<void> say(String zh, {String? en}) async => said.add(en == null ? zh : '$zh|$en');

  @override
  Future<void> stop() async => stops++;
}
