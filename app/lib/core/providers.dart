import 'dart:math' as math;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'content.dart';
import 'game.dart';
import 'scenes.dart';
import 'sounds.dart';
import 'store.dart';
import 'voice.dart';

/// What time it is (tests and screenshots set it).
final clockProvider = Provider<DateTime Function()>((ref) => DateTime.now);

/// Dice for the puzzles (tests give a seeded one).
final randomProvider = Provider<math.Random>((ref) => math.Random());

final storeProvider = Provider<GameStore>((ref) => MemoryStore());
final savedGameProvider = Provider<Game>((ref) => const Game());
final soundsProvider = Provider<Sounds>((ref) => const SilentSounds());
final voiceProvider = Provider<Voice>((ref) => const SilentVoice());

/// The places, read from assets/scenes/ once.
final sceneProvider = FutureProvider.family<Scene, Place>((ref, place) => Scene.load(place));

/// The game; every change is saved straight away.
final gameProvider = NotifierProvider<GameNotifier, Game>(GameNotifier.new);

class GameNotifier extends Notifier<Game> {
  /// The save, as the app opens: the sitting goes on if the app was closed
  /// for less than ten minutes (Game.opened).
  @override
  Game build() {
    final saved = ref.read(savedGameProvider);
    final opened = saved.opened(ref.read(clockProvider)());
    if (!identical(opened, saved)) ref.read(storeProvider).write(opened.toJson());
    return opened;
  }

  void change(Game Function(Game g) f) {
    final next = f(state);
    if (identical(next, state)) return;
    state = next;
    ref.read(storeProvider).write(next.toJson());
  }

  void settings(Settings Function(Settings s) f) => change((g) => g.copyWith(settings: f(g.settings)));
}

/// The style the child switched to with the palette button, for this time
/// only (null: the parent's 「一開始的畫風」, which it never changes).
final pickedStyleProvider = NotifierProvider<PickedStyle, Style?>(PickedStyle.new);

class PickedStyle extends Notifier<Style?> {
  @override
  Style? build() => null;

  void pick(Style? s) => state = s;
}

/// The style the pictures are drawn in now.
final styleProvider = Provider<Style>((ref) => ref.watch(pickedStyleProvider) ?? ref.watch(gameProvider.select((g) => g.settings.style)));

/// Things said only once per app start (the welcome on the home page).
final onceProvider = Provider<Set<String>>((ref) => <String>{});
