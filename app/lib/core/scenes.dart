import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/services.dart';

import 'content.dart';

/// A box on the 600×600 scene, as fractions of its side: the centre and
/// the size (docs/scenes.md).
class Box {
  const Box(this.x, this.y, this.w, this.h);

  final double x;
  final double y;
  final double w;
  final double h;

  double get left => x - w / 2;
  double get right => x + w / 2;
  double get top => y - h / 2;
  double get bottom => y + h / 2;

  /// [s] times as big, standing where it stood (the bottom edge stays).
  Box scaled(double s) => Box(x, bottom - h * s / 2, w * s, h * s);

  /// The smallest box holding both.
  Box union(Box o) {
    final l = math.min(left, o.left), r = math.max(right, o.right);
    final t = math.min(top, o.top), b = math.max(bottom, o.bottom);
    return Box((l + r) / 2, (t + b) / 2, r - l, b - t);
  }

  /// At least [min] wide and high, and [pad] more on every side.
  Box grown({double min = 0, double pad = 0}) => Box(x, y, math.max(w, min) + 2 * pad, math.max(h, min) + 2 * pad);

  /// Whether the two touch, keeping [gap] between them.
  bool overlaps(Box o, {double gap = 0}) =>
      left - gap < o.right && o.left - gap < right && top - gap < o.bottom && o.top - gap < bottom;

  bool contains(double px, double py) => px >= left && px <= right && py >= top && py <= bottom;

  double distance2(double px, double py) => (px - x) * (px - x) + (py - y) * (py - y);

  @override
  String toString() => 'Box(${x.toStringAsFixed(2)}, ${y.toStringAsFixed(2)}, ${w.toStringAsFixed(2)}, ${h.toStringAsFixed(2)})';
}

/// How a thing can change (docs/scenes.md `changes[].kind`).
enum ChangeKind { art, gone, flip, size, extra }

/// What kind of new drawing an `art` change is.
enum ArtType { color, swap, count, pattern, face }

/// One way 小變 can change a thing.
class Change {
  const Change({required this.kind, this.type, this.art, this.scale = 1, required this.said});

  final ChangeKind kind;
  final ArtType? type;

  /// The drawing it turns into (kind art).
  final String? art;

  /// How much bigger or smaller (kind size).
  final double scale;

  /// What 小變 says when it is found (read out).
  final String said;

  /// The youngest age this kind of change is used for (docs/design.md
  /// 「不一樣的種類」: 2～3 colour and gone/one more; 3～4 also direction,
  /// size and swaps; 4～5 everything).
  Level get from => switch (kind) {
        ChangeKind.gone || ChangeKind.extra => Level.small,
        ChangeKind.flip || ChangeKind.size => Level.mid,
        ChangeKind.art => switch (type) {
            ArtType.color || null => Level.small,
            ArtType.swap => Level.mid,
            ArtType.count || ArtType.pattern || ArtType.face => Level.big,
          },
      };

  /// A short name for the kind, to spread a puzzle over different kinds.
  String get sort => kind == ChangeKind.art ? 'art.${type?.name}' : kind.name;

  static Change? fromJson(Object? j) {
    if (j is! Map) return null;
    final kind = ChangeKind.values.asNameMap()[j['kind']];
    final said = j['said'];
    if (kind == null || kind == ChangeKind.extra || said is! String) return null;
    final art = j['art'];
    if (kind == ChangeKind.art && art is! String) return null;
    final scale = j['scale'];
    if (kind == ChangeKind.size && (scale is! num || scale <= 0)) return null;
    return Change(
      kind: kind,
      type: ArtType.values.asNameMap()[j['type']],
      art: art is String ? art : null,
      scale: scale is num ? scale.toDouble() : 1,
      said: said,
    );
  }
}

/// A thing in a scene: where it is, how it is drawn, how it can change.
/// Extras (things that only come in as 「多了一個」) have one change of
/// kind extra.
class Thing {
  const Thing({required this.id, required this.zh, required this.en, required this.box, required this.z, required this.big, required this.changes});

  final String id;
  final String zh;
  final String en;
  final Box box;
  final int z;

  /// Big and plain enough for a 2 year old.
  final bool big;
  final List<Change> changes;

  bool get extra => changes.length == 1 && changes.first.kind == ChangeKind.extra;

  static Thing? fromJson(Object? j, {bool extra = false}) {
    if (j is! Map) return null;
    final id = j['id'], zh = j['zh'], en = j['en'];
    final box = _box(j);
    if (id is! String || zh is! String || box == null) return null;
    final said = j['said'];
    if (extra && said is! String) return null;
    return Thing(
      id: id,
      zh: zh,
      en: en is String ? en : '',
      box: box,
      z: (j['z'] as num?)?.toInt() ?? 0,
      big: j['big'] == true,
      changes: extra
          ? [Change(kind: ChangeKind.extra, said: said as String)]
          : [for (final c in (j['changes'] is List ? j['changes'] as List : const [])) ?Change.fromJson(c)],
    );
  }
}

/// A place 小變 can hide, and the colour he turns there.
class Hide {
  const Hide({required this.box, required this.z, required this.tint});

  final Box box;
  final int z;
  final String tint;

  static Hide? fromJson(Object? j) {
    if (j is! Map) return null;
    final box = _box(j), tint = j['tint'];
    if (box == null || tint is! String) return null;
    return Hide(box: box, z: (j['z'] as num?)?.toInt() ?? 0, tint: tint);
  }
}

/// The row of same things for 「哪一個不一樣？」.
class Lineup {
  const Lineup({required this.art, required this.zh, required this.w, required this.h, required this.odd});

  final String art;
  final String zh;

  /// The drawing's size, as a box in the scene would have (only the shape matters).
  final double w;
  final double h;
  final List<Change> odd;

  static Lineup? fromJson(Object? j) {
    if (j is! Map) return null;
    final art = j['art'], zh = j['zh'], w = j['w'], h = j['h'];
    if (art is! String || zh is! String || w is! num || h is! num || w <= 0 || h <= 0) return null;
    final odd = [for (final c in (j['odd'] is List ? j['odd'] as List : const [])) ?Change.fromJson(c)];
    if (odd.isEmpty) return null;
    return Lineup(art: art, zh: zh, w: w.toDouble(), h: h.toDouble(), odd: odd);
  }
}

/// One place: its things, the extras, the hiding spots and the lineup
/// (assets/scenes/<place>.json, written with the drawings by design/art/).
class Scene {
  const Scene({required this.place, required this.things, required this.extras, required this.hides, required this.lineup});

  final Place place;
  final List<Thing> things;
  final List<Thing> extras;
  final List<Hide> hides;
  final Lineup lineup;

  Thing? thing(String id) => [...things, ...extras].where((t) => t.id == id).firstOrNull;

  factory Scene.fromJson(Place place, Map<String, dynamic> j) {
    final lineup = Lineup.fromJson(j['lineup']);
    if (lineup == null) throw FormatException('${place.name}: no lineup');
    return Scene(
      place: place,
      things: [for (final t in (j['objects'] as List? ?? const [])) ?Thing.fromJson(t)],
      extras: [for (final t in (j['extras'] as List? ?? const [])) ?Thing.fromJson(t, extra: true)],
      hides: [for (final h in (j['hides'] as List? ?? const [])) ?Hide.fromJson(h)],
      lineup: lineup,
    );
  }

  static Future<Scene> load(Place place, [AssetBundle? bundle]) async {
    final text = await (bundle ?? rootBundle).loadString('assets/scenes/${place.name}.json');
    return Scene.fromJson(place, jsonDecode(text) as Map<String, dynamic>);
  }
}

Box? _box(Map j) {
  final x = j['x'], y = j['y'], w = j['w'], h = j['h'];
  if (x is! num || y is! num || w is! num || h is! num || w <= 0 || h <= 0) return null;
  return Box(x.toDouble(), y.toDouble(), w.toDouble(), h.toDouble());
}

/// Where a drawing is (the art folder is per style).
String artPath(Style style, Place place, String art) => 'assets/art/${style.name}/${place.name}/$art.svg';

String backgroundPath(Style style, Place place) => artPath(style, place, 'bg');

/// 小變: wave, think, cheer, magic (and the hiding ones, hide_<tint>).
String chameleonPath(Style style, String pose) => 'assets/art/${style.name}/chameleon_$pose.svg';
