import 'dart:math' as math;

import 'content.dart';

/// What a parent set (parent mode).
class Settings {
  const Settings({
    this.level = Level.mid,
    this.minutes = 15,
    this.style = Style.a,
    this.hints = true,
    this.english = false,
    this.music = true,
    this.sounds = true,
    this.voice = true,
    this.full = true,
  });

  /// The child's age, which sets how hard the puzzles are.
  final Level level;

  /// How long one sitting may be before a rest.
  final int minutes;

  /// The drawing style (the child can switch it while playing too).
  final Style style;

  /// Many hints: 小變 shows where to look after 20 seconds without a find.
  final bool hints;
  final bool english;
  final bool music;
  final bool sounds;
  final bool voice;

  /// The full version (all places); on while testing.
  final bool full;

  static const minuteChoices = [5, 10, 15, 20, 30];

  /// A game shows when it suits the age (2～3 do not play two pictures).
  bool shows(Mode m) => m.from.index <= level.index;

  bool opens(Place p) => full || p.free;

  Settings copyWith({Level? level, int? minutes, Style? style, bool? hints, bool? english, bool? music, bool? sounds, bool? voice, bool? full}) => Settings(
        level: level ?? this.level,
        minutes: minutes ?? this.minutes,
        style: style ?? this.style,
        hints: hints ?? this.hints,
        english: english ?? this.english,
        music: music ?? this.music,
        sounds: sounds ?? this.sounds,
        voice: voice ?? this.voice,
        full: full ?? this.full,
      );

  Map<String, dynamic> toJson() => {
        'level': level.name,
        'minutes': minutes,
        'style': style.name,
        'hints': hints,
        'english': english,
        'music': music,
        'sounds': sounds,
        'voice': voice,
        'full': full,
      };

  factory Settings.fromJson(Map<String, dynamic> j) {
    final m = j['minutes'];
    bool flag(String k, bool d) => j[k] is bool ? j[k] as bool : d;
    return Settings(
      level: Level.values.asNameMap()[j['level']] ?? Level.mid,
      minutes: m is int && minuteChoices.contains(m) ? m : 15,
      style: Style.values.asNameMap()[j['style']] ?? Style.a,
      hints: flag('hints', true),
      english: flag('english', false),
      music: flag('music', true),
      sounds: flag('sounds', true),
      voice: flag('voice', true),
      full: flag('full', true),
    );
  }
}

/// Everything kept: the games done in each place, the differences found,
/// the rest and the settings. One small file (store.dart).
class Game {
  const Game({this.done = const {}, this.found = const {}, this.restSince, this.settings = const Settings()});

  /// The games played to the end in each place (a star each, three at most;
  /// the place goes into the album).
  final Map<Place, Set<Mode>> done;

  /// Differences found in each place (parent mode).
  final Map<Place, int> found;

  /// When the play time ran out (null: playing).
  final DateTime? restSince;
  final Settings settings;

  /// A rest lasts until a parent lets play go on, or an hour has passed.
  static const restLength = Duration(hours: 1);

  bool resting(DateTime now) => restSince != null && now.difference(restSince!) < restLength;

  int starsOf(Place p) => math.min(3, done[p]?.length ?? 0);

  /// In the album once a game there has been played to the end.
  bool inAlbum(Place p) => done[p]?.isNotEmpty ?? false;

  Game copyWith({Map<Place, Set<Mode>>? done, Map<Place, int>? found, DateTime? restSince, bool clearRest = false, Settings? settings}) => Game(
        done: done ?? this.done,
        found: found ?? this.found,
        restSince: clearRest ? null : (restSince ?? this.restSince),
        settings: settings ?? this.settings,
      );

  /// [n] more differences found in [p].
  Game spotted(Place p, [int n = 1]) => copyWith(found: {...found, p: (found[p] ?? 0) + n});

  /// A game of [m] in [p] played to the end.
  Game finished(Place p, Mode m) => copyWith(done: {...done, p: {...?done[p], m}});

  Game rest(DateTime now) => copyWith(restSince: now);

  Game playOn() => copyWith(clearRest: true);

  Map<String, dynamic> toJson() => {
        'version': 1,
        'done': {for (final e in done.entries) e.key.name: [for (final m in e.value) m.name]..sort()},
        'found': {for (final e in found.entries) e.key.name: e.value},
        if (restSince != null) 'restSince': restSince!.toIso8601String(),
        'settings': settings.toJson(),
      };

  factory Game.fromJson(Map<String, dynamic>? j) {
    if (j == null) return const Game();
    final done = j['done'], found = j['found'], rest = j['restSince'];
    return Game(
      done: {
        if (done is Map)
          for (final p in Place.values)
            if (done[p.name] is List) p: {for (final m in Mode.values) if ((done[p.name] as List).contains(m.name)) m},
      },
      found: {
        if (found is Map)
          for (final p in Place.values)
            if (found[p.name] is int && (found[p.name] as int) >= 0) p: found[p.name] as int,
      },
      restSince: rest is String ? DateTime.tryParse(rest) : null,
      settings: Settings.fromJson(j['settings'] is Map ? (j['settings'] as Map).cast<String, dynamic>() : const {}),
    );
  }
}
