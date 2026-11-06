import 'dart:math' as math;

import 'package:flutter_test/flutter_test.dart';
import 'package:sharp_eyes/core/content.dart';
import 'package:sharp_eyes/core/game.dart';
import 'package:sharp_eyes/core/puzzles.dart';
import 'package:sharp_eyes/core/scenes.dart';

/// A made-up place, so the rules are tested apart from the drawings.
Scene fixture() => Scene.fromJson(Place.park, {
      'objects': [
        for (var i = 0; i < 12; i++)
          {
            'id': 't$i',
            'zh': '東西$i',
            'en': 'thing $i',
            'x': 0.15 + (i % 4) * 0.23,
            'y': 0.2 + (i ~/ 4) * 0.3,
            'w': i.isEven ? 0.16 : 0.08,
            'h': i.isEven ? 0.16 : 0.08,
            'z': 10 + i,
            'big': i.isEven,
            'changes': [
              {'kind': 'art', 'type': 'color', 'art': 't${i}_blue', 'said': '變藍色了！'},
              {'kind': 'gone', 'said': '不見了！'},
              if (i % 3 == 0) {'kind': 'flip', 'said': '轉過去了！'},
              if (i % 3 == 1) {'kind': 'size', 'scale': 1.4, 'said': '變大了！'},
              if (i % 4 == 2) {'kind': 'art', 'type': 'count', 'art': 't${i}_two', 'said': '少了一個！'},
              {'kind': 'bogus', 'said': 'x'},
            ],
          },
      ],
      'extras': [
        {'id': 'bird', 'zh': '小鳥', 'en': 'bird', 'x': 0.5, 'y': 0.92, 'w': 0.14, 'h': 0.1, 'z': 90, 'big': true, 'said': '多了一隻小鳥！'},
        {'id': 'bad', 'zh': '壞的', 'x': 0.5, 'y': 0.92, 'w': 0.14, 'h': 0.1},
      ],
      'hides': [
        {'x': 0.3, 'y': 0.5, 'w': 0.1, 'h': 0.08, 'z': 40, 'tint': 'leaf'},
        {'x': 0.7, 'y': 0.8, 'w': 0.1, 'h': 0.08, 'z': 40, 'tint': 'sand'},
      ],
      'lineup': {
        'art': 'duck',
        'zh': '小鴨子',
        'w': 0.2,
        'h': 0.2,
        'odd': [
          {'kind': 'art', 'type': 'color', 'art': 'duck_blue', 'said': '這隻小鴨是藍色的！'},
          {'kind': 'flip', 'said': '這隻小鴨轉向另一邊！'},
        ],
      },
    });

void main() {
  test('a scene file is read, and broken entries are left out', () {
    final s = fixture();
    expect(s.things, hasLength(12));
    expect(s.extras.map((e) => e.id), ['bird']);
    expect(s.things.first.changes.map((c) => c.kind), isNot(contains(ChangeKind.extra)));
    expect(s.things.first.changes, hasLength(3), reason: 'colour, gone, flip; the bogus kind is dropped');
    expect(s.hides, hasLength(2));
    expect(s.lineup.odd, hasLength(2));
  });

  test('each level uses its kinds of change and size of thing', () {
    final s = fixture();
    for (final level in Level.values) {
      for (final d in Puzzles.choices(s, level)) {
        expect(d.change.from.index, lessThanOrEqualTo(level.index));
        if (level != Level.big) expect(d.thing.big, isTrue, reason: 'only big things before 4～5');
      }
    }
    final small = Puzzles.choices(s, Level.small).map((d) => d.change.kind).toSet();
    expect(small, {ChangeKind.art, ChangeKind.gone, ChangeKind.extra});
    expect(Puzzles.choices(s, Level.small).where((d) => d.change.kind == ChangeKind.art).every((d) => d.change.type == ArtType.color), isTrue);
    expect(Puzzles.choices(s, Level.mid).map((d) => d.change.kind).toSet(), containsAll([ChangeKind.flip, ChangeKind.size]));
    expect(Puzzles.choices(s, Level.big).any((d) => d.change.type == ArtType.count), isTrue);
    expect(Puzzles.choices(s, Level.big).any((d) => !d.thing.big), isTrue);
  });

  test('the differences of one puzzle are one per thing and never overlap', () {
    final s = fixture();
    for (var seed = 0; seed < 200; seed++) {
      final r = math.Random(seed);
      for (final level in [Level.mid, Level.big]) {
        final two = TwoRound.deal(s, level, r);
        expect(two.diffs, hasLength(TwoRound.count(level)));
        expect(two.diffs.map((d) => d.thing.id).toSet(), hasLength(two.diffs.length));
        for (final a in two.diffs) {
          for (final b in two.diffs) {
            if (!identical(a, b)) expect(a.box.overlaps(b.box, gap: Puzzles.gap), isFalse);
          }
        }
      }
    }
  });

  test('a puzzle spreads over different kinds of change', () {
    final s = fixture();
    final kinds = TwoRound.deal(s, Level.big, math.Random(3)).diffs.map((d) => d.change.sort).toSet();
    expect(kinds.length, greaterThanOrEqualTo(4));
  });

  test('the changed picture shows each change', () {
    final s = fixture();
    final t0 = s.things[0], t1 = s.things[1], t2 = s.things[2], t3 = s.things[3];
    final bird = s.extras.single;
    Change of(Thing t, ChangeKind k) => t.changes.firstWhere((c) => c.kind == k);
    final diffs = [
      Diff(t0, of(t0, ChangeKind.flip)),
      Diff(t1, of(t1, ChangeKind.size)),
      Diff(t2, of(t2, ChangeKind.art)),
      Diff(t3, of(t3, ChangeKind.gone)),
      Diff(bird, bird.changes.single),
    ];
    final before = Picture.of(s), after = before.changed(diffs);
    expect(after.sprite('t0')!.flip, isTrue);
    expect(after.sprite('t1')!.box.w, closeTo(t1.box.w * 1.4, 1e-9));
    expect(after.sprite('t1')!.box.bottom, closeTo(t1.box.bottom, 1e-9), reason: 'it grows standing where it stood');
    expect(after.sprite('t2')!.art, 't2_blue');
    expect(after.sprite('t3'), isNull);
    expect(after.sprite('bird'), isNotNull);
    expect(before.sprite('bird'), isNull);
    expect(after.sprites.map((p) => p.z).toList(), orderedEquals([...after.sprites.map((p) => p.z)]..sort()));
    // A thing that grew is found anywhere in its old or new size.
    expect(diffs[1].box.w, closeTo(t1.box.w * 1.4, 1e-9));
  });

  test('a tap finds the nearest difference, with room for small fingers', () {
    final s = fixture();
    final small = s.things[1]; // 0.08 wide
    final d = Diff(small, small.changes.first);
    final ds = [d];
    expect(Puzzles.hit(ds, small.box.x, small.box.y), d);
    // Just outside the drawing, still inside the bigger target.
    expect(Puzzles.hit(ds, small.box.right + 0.04, small.box.y), d);
    expect(Puzzles.hit(ds, small.box.right + 0.2, small.box.y), isNull);
    expect(Puzzles.hit(ds, small.box.x, small.box.y, found: {d}), isNull, reason: 'found ones are not found again');
  });

  test('the odd one out: three, four, five in a row; turning round from 3～4', () {
    final s = fixture();
    for (var seed = 0; seed < 50; seed++) {
      final r = math.Random(seed);
      final small = OddRound.deal(s, Level.small, r);
      expect(small.count, 3);
      expect(small.odd, inInclusiveRange(0, 2));
      expect(small.change.kind, ChangeKind.art);
      expect(OddRound.deal(s, Level.mid, r).count, 4);
      expect(OddRound.deal(s, Level.big, r).count, 5);
    }
    expect({for (var seed = 0; seed < 50; seed++) OddRound.deal(s, Level.mid, math.Random(seed)).change.kind}, containsAll([ChangeKind.art, ChangeKind.flip]));
  });

  test('what changed: one that sparkles for 2～3, two to remember after', () {
    final s = fixture();
    final small = ChangeRound.deal(s, Level.small, math.Random(1));
    expect(small.diffs, hasLength(1));
    expect(small.flash, isTrue);
    final mid = ChangeRound.deal(s, Level.mid, math.Random(1));
    expect(mid.diffs, hasLength(2));
    expect(mid.flash, isFalse);
  });

  test('hide and seek: a new spot each time, plainer for the youngest', () {
    final s = fixture();
    final first = HideRound.deal(s, Level.small, math.Random(1));
    for (var seed = 0; seed < 20; seed++) {
      expect(HideRound.deal(s, Level.small, math.Random(seed), not: first.hide).hide, isNot(first.hide));
    }
    expect(first.onTop, isTrue);
    expect(first.box.w, greaterThan(first.hide.box.w));
    final big = HideRound.deal(s, Level.big, math.Random(1));
    expect(big.onTop, isFalse);
    expect(big.box.w, lessThan(big.hide.box.w));
    expect(big.art, startsWith('hide_'));
  });

  test('settings and progress are kept, and a damaged save does not break the game', () {
    final g = const Game(settings: Settings(level: Level.big, minutes: 20, style: Style.c, hints: false, english: true))
        .finished(Place.park, Mode.odd)
        .finished(Place.park, Mode.hide)
        .finished(Place.park, Mode.hide)
        .spotted(Place.beach, 4)
        .rest(DateTime(2026, 11, 6, 10));
    final back = Game.fromJson(g.toJson());
    expect(back.settings.level, Level.big);
    expect(back.settings.minutes, 20);
    expect(back.settings.style, Style.c);
    expect(back.settings.hints, isFalse);
    expect(back.settings.english, isTrue);
    expect(back.starsOf(Place.park), 2);
    expect(back.inAlbum(Place.park), isTrue);
    expect(back.inAlbum(Place.zoo), isFalse);
    expect(back.found[Place.beach], 4);
    expect(back.resting(DateTime(2026, 11, 6, 10, 30)), isTrue);
    expect(back.resting(DateTime(2026, 11, 6, 11, 1)), isFalse);

    final broken = Game.fromJson({
      'done': {'park': 'odd', 'zoo': ['odd', 7, 'nope']},
      'found': {'park': -3, 'beach': 'x'},
      'restSince': 12,
      'settings': {'level': 'huge', 'minutes': 7, 'style': 'z', 'hints': 'yes'},
    });
    expect(broken.done.keys, [Place.zoo]);
    expect(broken.done[Place.zoo], {Mode.odd});
    expect(broken.found, isEmpty);
    expect(broken.restSince, isNull);
    expect(broken.settings.level, Level.mid);
    expect(broken.settings.minutes, 15);
    expect(broken.settings.style, Style.a);
    expect(broken.settings.hints, isTrue);
  });

  test('2～3 year olds do not get two pictures; stars stop at three', () {
    expect(const Settings(level: Level.small).shows(Mode.two), isFalse);
    expect(const Settings(level: Level.small).shows(Mode.hide), isTrue);
    expect(const Settings(level: Level.mid).shows(Mode.two), isTrue);
    var g = const Game();
    for (final m in Mode.values) {
      g = g.finished(Place.zoo, m);
    }
    expect(g.starsOf(Place.zoo), 3);
    expect(Style.c.next, Style.a);
    expect(const Settings(full: false).opens(Place.zoo), isFalse);
    expect(const Settings(full: false).opens(Place.beach), isTrue);
  });
}
