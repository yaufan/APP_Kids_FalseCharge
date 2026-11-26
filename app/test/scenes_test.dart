import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart' show RenderRepaintBoundary;
import 'package:flutter_test/flutter_test.dart';
import 'package:sharp_eyes/app/widgets.dart';
import 'package:sharp_eyes/core/content.dart';
import 'package:sharp_eyes/core/puzzles.dart';
import 'package:sharp_eyes/core/scenes.dart';
import 'package:sharp_eyes/features/play/scene_view.dart';

/// The drawings and the scene files agree (docs/scenes.md), and every place
/// can make the puzzles every age needs.
void main() {
  Scene read(Place p) => Scene.fromJson(p, jsonDecode(File('assets/scenes/${p.name}.json').readAsStringSync()) as Map<String, dynamic>);

  void exists(String path) => expect(File(path).existsSync(), isTrue, reason: path);

  test('小變 is drawn in every style and pose', () {
    final tints = {for (final p in Place.values) for (final h in read(p).hides) h.tint};
    for (final s in Style.values) {
      for (final pose in ['wave', 'think', 'cheer', 'magic', 'sleep', for (final t in tints) 'hide_$t']) {
        exists(chameleonPath(s, pose));
      }
    }
  });

  testWidgets('小變 never hides completely: even for 4～5 a bit of him shows at every spot', (tester) async {
    // Drawn with the real flutter_svg: the scene with him hiding, and with
    // him on top of everything; the part that shows is what differs from
    // the scene without him. (The three styles share one geometry.)
    tester.view.physicalSize = const Size(600, 600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final key = GlobalKey();
    Future<Uint8List> draw(Widget w) async {
      await tester.pumpWidget(MaterialApp(home: Align(alignment: Alignment.topLeft, child: RepaintBoundary(key: key, child: SizedBox.square(dimension: 600, child: w)))));
      for (var i = 0; i < 8; i++) {
        await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 30)));
        await tester.pump(const Duration(milliseconds: 20));
      }
      return (await tester.runAsync(() async {
        final image = await (key.currentContext!.findRenderObject()! as RenderRepaintBoundary).toImage();
        return (await image.toByteData(format: ui.ImageByteFormat.rawRgba))!.buffer.asUint8List();
      }))!;
    }

    int differ(Uint8List a, Uint8List b) {
      var n = 0;
      for (var i = 0; i < a.length; i += 4) {
        if ((a[i] - b[i]).abs() + (a[i + 1] - b[i + 1]).abs() + (a[i + 2] - b[i + 2]).abs() > 24) n++;
      }
      return n;
    }

    for (final place in Place.values) {
      final scene = read(place), picture = Picture.of(scene);
      Widget view([Layer? l]) => SceneView(picture: picture, style: Style.a, side: 600, radius: 0, layers: [?l]);
      final bare = await draw(view());
      for (final hide in scene.hides) {
        final r = HideRound(scene: scene, hide: hide, level: Level.big);
        Widget him() => Art(chameleonPath(Style.a, r.art), fit: BoxFit.fill);
        final shows = differ(bare, await draw(view(Layer(r.box, him(), z: hide.z))));
        final all = differ(bare, await draw(view(Layer(r.box, him()))));
        expect(shows / all, greaterThan(0.2), reason: '${place.name} ${hide.tint}: $shows of $all');
      }
    }
  });

  for (final place in Place.values) {
    group(place.name, () {
      test('every thing, change and extra has its drawing in all three styles', () {
        final s = read(place);
        final raw = jsonDecode(File('assets/scenes/${place.name}.json').readAsStringSync()) as Map<String, dynamic>;
        expect(s.things, hasLength((raw['objects'] as List).length), reason: 'nothing in the file is dropped');
        expect(s.extras, hasLength((raw['extras'] as List).length));
        for (final style in Style.values) {
          exists(backgroundPath(style, place));
          for (final t in [...s.things, ...s.extras]) {
            exists(artPath(style, place, t.id));
            for (final c in t.changes) {
              if (c.art != null) exists(artPath(style, place, c.art!));
            }
          }
          exists(artPath(style, place, s.lineup.art));
          for (final c in s.lineup.odd) {
            if (c.art != null) exists(artPath(style, place, c.art!));
          }
        }
      });

      test('things sit inside the picture and each can change', () {
        final s = read(place);
        expect(s.things.length, greaterThanOrEqualTo(12));
        expect(s.extras, isNotEmpty);
        expect(s.hides.length, greaterThanOrEqualTo(3));
        for (final t in [...s.things, ...s.extras]) {
          expect(t.changes, isNotEmpty, reason: t.id);
          for (final b in [t.box, for (final c in t.changes) if (c.kind == ChangeKind.size) t.box.scaled(c.scale)]) {
            expect(b.left, greaterThanOrEqualTo(-0.001), reason: t.id);
            expect(b.top, greaterThanOrEqualTo(-0.001), reason: t.id);
            expect(b.right, lessThanOrEqualTo(1.001), reason: t.id);
            expect(b.bottom, lessThanOrEqualTo(1.001), reason: t.id);
          }
          for (final c in t.changes) {
            expect(c.said, isNotEmpty, reason: t.id);
          }
          if (t.big) expect(math.max(t.box.w, t.box.h), greaterThanOrEqualTo(0.1), reason: '${t.id} is big enough to see');
        }
        expect({for (final t in [...s.things, ...s.extras]) t.id}, hasLength(s.things.length + s.extras.length), reason: 'ids are unique');
      });

      test('every age gets its full puzzle, always', () {
        final s = read(place);
        for (var seed = 0; seed < 300; seed++) {
          final r = math.Random(seed);
          expect(ChangeRound.deal(s, Level.small, r).diffs, hasLength(1));
          expect(ChangeRound.deal(s, Level.mid, r).diffs, hasLength(2));
          expect(TwoRound.deal(s, Level.mid, r).diffs, hasLength(3), reason: 'seed $seed');
          expect(TwoRound.deal(s, Level.big, r).diffs, hasLength(5), reason: 'seed $seed');
        }
        // 2～3 year olds see colour, gone and one more.
        final small = Puzzles.choices(s, Level.small);
        expect(small.map((d) => d.change.kind).toSet(), containsAll([ChangeKind.art, ChangeKind.gone]));
        // Older children meet every kind there is.
        final big = Puzzles.choices(s, Level.big).map((d) => d.change.sort).toSet();
        expect(big.length, greaterThanOrEqualTo(5));
        // The odd one out has something for the youngest.
        expect(s.lineup.odd.where((c) => c.from == Level.small), isNotEmpty);
      });
    });
  }
}
