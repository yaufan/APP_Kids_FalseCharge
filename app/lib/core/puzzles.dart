import 'dart:math' as math;

import 'content.dart';
import 'scenes.dart';

/// One thing as a picture draws it.
class Sprite {
  const Sprite({required this.id, required this.art, required this.box, required this.z, this.flip = false});

  /// The thing's id (several sprites can share a drawing).
  final String id;
  final String art;
  final Box box;
  final int z;

  /// Drawn the other way round (left and right swapped).
  final bool flip;

  Sprite copyWith({String? art, Box? box, bool? flip}) => Sprite(id: id, art: art ?? this.art, box: box ?? this.box, z: z, flip: flip ?? this.flip);
}

/// A picture of a place: the background and its things, drawn from the
/// lowest z up.
class Picture {
  Picture(this.place, Iterable<Sprite> sprites) : sprites = List.unmodifiable([...sprites]..sort((a, b) => a.z.compareTo(b.z)));

  final Place place;
  final List<Sprite> sprites;

  /// The place as it is before 小變 does anything.
  factory Picture.of(Scene s) => Picture(s.place, [for (final t in s.things) Sprite(id: t.id, art: t.id, box: t.box, z: t.z)]);

  Sprite? sprite(String id) => sprites.where((s) => s.id == id).firstOrNull;

  /// The picture with the [diffs] made.
  Picture changed(Iterable<Diff> diffs) {
    final byId = {for (final s in sprites) s.id: s};
    for (final d in diffs) {
      final c = d.change, t = d.thing;
      switch (c.kind) {
        case ChangeKind.art:
          final s = byId[t.id];
          if (s != null) byId[t.id] = s.copyWith(art: c.art);
        case ChangeKind.gone:
          byId.remove(t.id);
        case ChangeKind.flip:
          final s = byId[t.id];
          if (s != null) byId[t.id] = s.copyWith(flip: !s.flip);
        case ChangeKind.size:
          final s = byId[t.id];
          if (s != null) byId[t.id] = s.copyWith(box: s.box.scaled(c.scale));
        case ChangeKind.extra:
          byId[t.id] = Sprite(id: t.id, art: t.id, box: t.box, z: t.z);
      }
    }
    return Picture(place, byId.values);
  }
}

/// A difference to find: the thing, what happened to it and the area a
/// tap finds it in.
class Diff {
  Diff(this.thing, this.change) : box = change.kind == ChangeKind.size ? thing.box.union(thing.box.scaled(change.scale)) : thing.box;

  final Thing thing;
  final Change change;

  /// Where it is on the scene (before and after).
  final Box box;

  String get said => change.said;

  /// What a finger can touch to find it: small things get a bigger target
  /// (small fingers are not precise).
  Box get target => box.grown(min: Puzzles.minTarget, pad: Puzzles.slack);
}

/// The differences a level uses (docs/design.md 「不一樣的種類」, docs/scenes.md 「難度怎麼用」).
abstract final class Puzzles {
  /// A tap this close to a difference finds it.
  static const slack = 0.02;

  /// The smallest target, as a part of the picture's side.
  static const minTarget = 0.13;

  /// Room between two differences of one puzzle.
  static const gap = 0.015;

  /// Whether [t] may be changed for a child of [level]: the small ones
  /// only from 4～5.
  static bool fits(Thing t, Level level) => t.big || level == Level.big;

  /// Every difference the scene offers at [level].
  static List<Diff> choices(Scene s, Level level) => [
        for (final t in [...s.things, ...s.extras])
          if (fits(t, level))
            for (final c in t.changes)
              if (c.from.index <= level.index) Diff(t, c),
      ];

  /// [n] differences that are far enough apart, one per thing, of as many
  /// different kinds as there are. Fewer if the scene has not enough.
  static List<Diff> pick(Scene s, Level level, int n, math.Random r) {
    final all = choices(s, level)..shuffle(r);
    final picked = <Diff>[];
    bool free(Diff d) => picked.every((p) => p.thing.id != d.thing.id && !p.box.overlaps(d.box, gap: gap));
    // First different kinds, then anything that fits.
    for (final anyKind in [false, true]) {
      for (final d in all) {
        if (picked.length == n) return picked;
        if (picked.contains(d) || !free(d)) continue;
        if (!anyKind && picked.any((p) => p.change.sort == d.change.sort)) continue;
        picked.add(d);
      }
    }
    return picked;
  }

  /// Which of [diffs] (not yet [found]) a tap at ([x], [y]) finds: the
  /// nearest whose target holds the tap.
  static Diff? hit(List<Diff> diffs, double x, double y, {Set<Diff> found = const {}}) {
    Diff? best;
    for (final d in diffs) {
      if (found.contains(d) || !d.target.contains(x, y)) continue;
      if (best == null || d.box.distance2(x, y) < best.box.distance2(x, y)) best = d;
    }
    return best;
  }

  /// The thing the finger is on in [p] (the one drawn on top), to say its name.
  static Sprite? touched(Picture p, double x, double y) {
    for (final s in p.sprites.reversed) {
      if (s.box.contains(x, y)) return s;
    }
    return null;
  }
}

/// 「哪一個不一樣？」: a row of the same thing, one of them different.
class OddRound {
  OddRound({required this.scene, required this.count, required this.odd, required this.change});

  /// Three in a row for 2～3, four for 3～4, five for 4～5.
  factory OddRound.deal(Scene s, Level level, math.Random r) {
    final changes = [for (final c in s.lineup.odd) if (c.from.index <= level.index) c];
    final pool = changes.isEmpty ? s.lineup.odd : changes;
    final count = level.pick(3, 4, 5);
    return OddRound(scene: s, count: count, odd: r.nextInt(count), change: pool[r.nextInt(pool.length)]);
  }

  final Scene scene;
  final int count;

  /// Which one is different.
  final int odd;
  final Change change;

  Lineup get lineup => scene.lineup;

  String get said => change.said;
}

/// 「小變變了什麼？」: the place, then 小變 says 「變！」 and changes things.
class ChangeRound {
  ChangeRound({required this.scene, required this.diffs, required this.flash}) : before = Picture.of(scene), after = Picture.of(scene).changed(diffs);

  /// One big change that sparkles as it happens for 2～3; two that the
  /// child has to remember for 3～4 and 4～5.
  factory ChangeRound.deal(Scene s, Level level, math.Random r) =>
      ChangeRound(scene: s, diffs: Puzzles.pick(s, level, level.pick(1, 2, 2), r), flash: level == Level.small);

  final Scene scene;
  final List<Diff> diffs;
  final bool flash;
  final Picture before;
  final Picture after;
}

/// 「兩張找不同」: the place twice, the bottom one with 3 (3～4) or 5 (4～5)
/// differences.
class TwoRound {
  TwoRound({required this.scene, required this.diffs}) : top = Picture.of(scene), bottom = Picture.of(scene).changed(diffs);

  factory TwoRound.deal(Scene s, Level level, math.Random r) => TwoRound(scene: s, diffs: Puzzles.pick(s, level, count(level), r));

  static int count(Level level) => level.pick(3, 3, 5);

  final Scene scene;
  final List<Diff> diffs;
  final Picture top;
  final Picture bottom;
}

/// 「小變躲在哪裡？」: 小變 hides in the place, the colour of where he is.
class HideRound {
  HideRound({required this.scene, required this.hide, required this.level}) : picture = Picture.of(scene);

  factory HideRound.deal(Scene s, Level level, math.Random r, {Hide? not}) {
    final spots = [for (final h in s.hides) if (h != not) h];
    final pool = spots.isEmpty ? s.hides : spots;
    return HideRound(scene: s, hide: pool[r.nextInt(pool.length)], level: level);
  }

  final Scene scene;
  final Hide hide;
  final Level level;
  final Picture picture;

  /// 2～3: in front of everything and a bit bigger, so he shows a lot;
  /// 4～5: a bit smaller, behind what is in front of the spot.
  double get scale => level.pick(1.25, 1.0, 0.85);
  bool get onTop => level == Level.small;

  Box get box => hide.box.scaled(scale);

  /// Where a tap finds him.
  Box get target => box.grown(min: Puzzles.minTarget, pad: Puzzles.slack);

  String get art => 'hide_${hide.tint}';
}
