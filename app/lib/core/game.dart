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

/// The sitting going on (docs/design.md 「每次玩多久」): the play time used
/// so far and when the app was last in sight. Kept in the save, so closing
/// the app and opening it again within ten minutes goes on with the same
/// sitting (the time it was closed does not count); after ten minutes or
/// more it is a new sitting.
class Sitting {
  const Sitting({this.played = Duration.zero, this.seen});

  final Duration played;
  final DateTime? seen;

  Map<String, dynamic> toJson() => {
        'played': played.inSeconds,
        if (seen != null) 'seen': seen!.toIso8601String(),
      };

  factory Sitting.fromJson(Object? j) {
    if (j is! Map) return const Sitting();
    final played = j['played'], seen = j['seen'];
    return Sitting(
      played: Duration(seconds: played is int && played > 0 ? played : 0),
      seen: seen is String ? DateTime.tryParse(seen) : null,
    );
  }
}

/// The parent gate's wait after wrong answers: three wrong in a row and it
/// waits 1 minute, the next time 5, then 15 (until a right answer). Kept in
/// the save, so closing the app does not end it.
class GateLock {
  const GateLock({this.misses = 0, this.locks = 0, this.from, this.until});

  /// Wrong answers since the last wait (or right answer).
  final int misses;

  /// Waits since the last right answer.
  final int locks;
  final DateTime? from;
  final DateTime? until;

  static const missesToLock = 3;
  static const waits = [Duration(minutes: 1), Duration(minutes: 5), Duration(minutes: 15)];

  bool locked(DateTime now) => until != null && now.isBefore(until!);

  /// How long there is still to wait.
  Duration left(DateTime now) => locked(now) ? until!.difference(now) : Duration.zero;

  GateLock miss(DateTime now) {
    if (misses + 1 < missesToLock) return GateLock(misses: misses + 1, locks: locks, from: from, until: until);
    final wait = waits[math.min(locks, waits.length - 1)];
    return GateLock(locks: locks + 1, from: now, until: now.add(wait));
  }

  /// The phone's clock was moved back to before the wait began: the wait
  /// starts again from now (never longer than it was), so it cannot last
  /// for ever.
  GateLock checked(DateTime now) {
    final f = from, u = until;
    if (f == null || u == null || !now.isBefore(f)) return this;
    return GateLock(misses: misses, locks: locks, from: now, until: now.add(u.difference(f)));
  }

  Map<String, dynamic> toJson() => {
        'misses': misses,
        'locks': locks,
        if (from != null) 'from': from!.toIso8601String(),
        if (until != null) 'until': until!.toIso8601String(),
      };

  factory GateLock.fromJson(Object? j) {
    if (j is! Map) return const GateLock();
    int count(Object? v) => v is int && v > 0 ? v : 0;
    DateTime? time(Object? v) => v is String ? DateTime.tryParse(v) : null;
    final from = time(j['from']), until = time(j['until']);
    return GateLock(
      misses: math.min(count(j['misses']), missesToLock - 1),
      locks: count(j['locks']),
      from: from != null && until != null ? from : null,
      until: from != null && until != null ? until : null,
    );
  }
}

/// Everything kept: the games done in each place, the differences found,
/// the rest and the settings. One small file (store.dart).
class Game {
  const Game({this.done = const {}, this.found = const {}, this.restSince, this.sitting = const Sitting(), this.gate = const GateLock(), this.settings = const Settings()});

  /// The games played to the end in each place (a star each, three at most;
  /// the place goes into the album).
  final Map<Place, Set<Mode>> done;

  /// Differences found in each place (parent mode).
  final Map<Place, int> found;

  /// When the play time ran out (null: playing).
  final DateTime? restSince;

  /// The play time used in this sitting.
  final Sitting sitting;

  /// The parent gate's wait after wrong answers.
  final GateLock gate;
  final Settings settings;

  /// A rest lasts until a parent lets play go on, or an hour has passed.
  static const restLength = Duration(hours: 1);

  /// Away from the app this long (closed or in the background) and the
  /// next time is a new sitting.
  static const awayIsRest = Duration(minutes: 10);

  bool resting(DateTime now) => restSince != null && now.difference(restSince!) < restLength;

  int starsOf(Place p) => math.min(3, done[p]?.length ?? 0);

  /// In the album once a game there has been played to the end.
  bool inAlbum(Place p) => done[p]?.isNotEmpty ?? false;

  Game copyWith({Map<Place, Set<Mode>>? done, Map<Place, int>? found, DateTime? restSince, bool clearRest = false, Sitting? sitting, GateLock? gate, Settings? settings}) => Game(
        done: done ?? this.done,
        found: found ?? this.found,
        restSince: clearRest ? null : (restSince ?? this.restSince),
        sitting: sitting ?? this.sitting,
        gate: gate ?? this.gate,
        settings: settings ?? this.settings,
      );

  /// [n] more differences found in [p].
  Game spotted(Place p, [int n = 1]) => copyWith(found: {...found, p: (found[p] ?? 0) + n});

  /// A game of [m] in [p] played to the end.
  Game finished(Place p, Mode m) => copyWith(done: {...done, p: {...?done[p], m}});

  /// The play time ran out: the rest begins (and the next sitting starts
  /// from nothing).
  Game rest(DateTime now) => copyWith(restSince: now, sitting: Sitting(seen: now));

  /// A parent let play go on, or the rest is over: a new sitting.
  Game playOn() => copyWith(clearRest: true, sitting: Sitting(seen: sitting.seen));

  /// [d] more play time in this sitting, saved at [now].
  Game played(Duration d, DateTime now) => copyWith(sitting: Sitting(played: sitting.played + d, seen: now));

  /// Away for ten minutes or more: a new sitting.
  Game newSitting(DateTime now) => copyWith(sitting: Sitting(seen: now));

  /// The phone's clock was moved back by [d]: the rest (and when the app
  /// was last seen) move back with it, so the rest neither ends early nor
  /// lasts longer.
  Game clockBack(Duration d) {
    if (d <= Duration.zero) return this;
    final seen = sitting.seen;
    return copyWith(restSince: restSince?.subtract(d), sitting: Sitting(played: sitting.played, seen: seen?.subtract(d)));
  }

  /// The app was opened (at [now]) with this save: within ten minutes of
  /// when it was last in sight it goes on with the same sitting, later it
  /// is a new one. A clock that is now before the last time it was seen was
  /// moved back: the time closed is not known, so the sitting goes on and
  /// the rest moves back with the clock.
  Game opened(DateTime now) {
    final seen = sitting.seen;
    if (seen == null) return this;
    final away = now.difference(seen);
    if (away.isNegative) return clockBack(-away);
    if (away >= awayIsRest) return newSitting(now);
    return this;
  }

  Map<String, dynamic> toJson() => {
        'version': 1,
        'done': {for (final e in done.entries) e.key.name: [for (final m in e.value) m.name]..sort()},
        'found': {for (final e in found.entries) e.key.name: e.value},
        if (restSince != null) 'restSince': restSince!.toIso8601String(),
        'sitting': sitting.toJson(),
        'gate': gate.toJson(),
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
      sitting: Sitting.fromJson(j['sitting']),
      gate: GateLock.fromJson(j['gate']),
      settings: Settings.fromJson(j['settings'] is Map ? (j['settings'] as Map).cast<String, dynamic>() : const {}),
    );
  }
}
