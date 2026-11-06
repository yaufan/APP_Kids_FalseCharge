import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sharp_eyes/app/strings.dart';
import 'package:sharp_eyes/core/content.dart';
import 'package:sharp_eyes/core/game.dart';
import 'package:sharp_eyes/core/puzzles.dart';
import 'package:sharp_eyes/core/scenes.dart';
import 'package:sharp_eyes/features/play/change_game.dart';
import 'package:sharp_eyes/features/play/play_screen.dart';
import 'package:sharp_eyes/features/play/scene_view.dart';

import 'helpers.dart';

/// The whole app played through, on a phone and a tablet, with screenshots
/// in build/screenshots/ (docs: CLAUDE.md 「完整流程和截圖」).
void main() {
  setUpAll(loadFonts);

  for (final (device, size, ratio) in [('phone', const Size(1080, 2340), 2.75), ('tablet', const Size(1620, 2160), 2.0)]) {
    testWidgets('the four games, the album, rest and parent mode ($device)', (tester) async {
      final app = await TestApp.start(tester, size: size, ratio: ratio);
      final flow = Flow(app);
      await flow.shot(device, '01_home');

      await app.tapLabel(Place.park.zh, ms: 1200);
      expect(app.location, '/place/park');
      await flow.shot(device, '02_place');

      // 哪一個不一樣？ A whole game: three rounds, a star, the album.
      await app.tapLabel(Mode.odd.zh, ms: 1500);
      expect(app.location, '/play/park/odd');
      await flow.shot(device, '03_odd');
      for (var r = 0; r < PlayBoard.rounds(Mode.odd); r++) {
        final odd = flow.round as OddRound;
        if (r == 0) {
          await tester.tap(find.byKey(ValueKey('odd-${(odd.odd + 1) % odd.count}')));
          await app.settle();
          expect(app.sounds.played.last, 'miss');
        }
        await tester.tap(find.byKey(ValueKey('odd-${odd.odd}')));
        await app.settle(600);
        if (r == 0) await flow.shot(device, '04_odd_found');
        await flow.wait(3);
      }
      expect(find.text(Strings.allFound), findsWidgets);
      expect(app.game.starsOf(Place.park), 1);
      expect(app.game.inAlbum(Place.park), isTrue);
      await flow.shot(device, '05_finished');
      await app.tapLabel(Strings.toHome, ms: 1200);
      expect(app.location, '/place/park');

      // 小變變了什麼？ Look, the magic, then find the change.
      await app.tapLabel(Mode.change.zh, ms: 1500);
      final change = flow.round as ChangeRound;
      expect(change.diffs, hasLength(2), reason: '3～4 remember two');
      await flow.shot(device, '06_change_look');
      await flow.wait(ChangeGame.lookFor(change).inMilliseconds / 1000 + 0.4);
      expect(app.sounds.played, contains('magic'));
      await flow.shot(device, '07_change_magic');
      await flow.wait(ChangeGame.magic.inMilliseconds / 1000 + 0.3);
      await flow.tapDiff(change.diffs.first);
      await flow.shot(device, '08_change_found');
      await flow.tapDiff(change.diffs.last);
      await flow.wait(3);
      await app.tapLabel(Strings.home, ms: 1000);

      // 兩張找不同: three differences, found on either picture.
      await app.tapLabel(Mode.two.zh, ms: 1500);
      final two = flow.round as TwoRound;
      expect(two.diffs, hasLength(3));
      await flow.shot(device, '09_two');
      await flow.tapAt(0, 0.02, 0.98);
      expect(app.sounds.played.last, 'miss');
      for (final (i, d) in two.diffs.indexed) {
        await flow.tapDiff(d, picture: i.isEven ? 1 : 0);
        if (i == 1) await flow.shot(device, '10_two_found');
      }
      await app.settle(600);
      expect(app.sounds.played, contains('all_found'));

      // Another style, the same puzzle.
      await app.tapLabel(Strings.switchStyle, ms: 1000);
      expect(app.game.settings.style, Style.b);
      await flow.shot(device, '11_two_style_b');
      await app.tapLabel(Strings.switchStyle, ms: 1000);
      expect(app.game.settings.style, Style.c);
      await flow.shot(device, '12_two_style_c');
      await flow.wait(3);
      await app.tapLabel(Strings.toHome, ms: 1200);
      await app.tapLabel(Strings.switchStyle, ms: 600);
      expect(app.game.settings.style, Style.a);

      // 小變躲在哪裡？ With a hint.
      await app.tapLabel(Mode.hide.zh, ms: 1500);
      final hide = flow.round as HideRound;
      await flow.shot(device, '13_hide');
      await app.tapLabel(Strings.hint, ms: 800);
      expect(app.sounds.played.last, 'hint');
      await flow.shot(device, '14_hide_hint');
      await flow.tapBox(hide.box);
      expect(app.sounds.played, contains('giggle'));
      await flow.shot(device, '15_hide_found');
      await app.tapLabel(Strings.home, ms: 1000);
      await app.tapLabel(Strings.home, ms: 1000);
      expect(app.location, '/');
      await flow.shot(device, '16_home_stars');

      // The album.
      await app.tapLabel(Strings.album, ms: 1000);
      await flow.shot(device, '17_album');
      await app.tapLabel(Strings.home, ms: 800);

      // Parent mode, through the gate.
      await app.tapLabel(Strings.parent, ms: 800);
      await flow.answerGate();
      expect(app.location, '/parent');
      await flow.shot(device, '18_parent');
      await tester.tap(find.byKey(const ValueKey('level-small')));
      await app.settle();
      expect(app.game.settings.level, Level.small);
      await tester.tap(find.byTooltip(Strings.back));
      await app.settle();

      // The play time runs out: 小變 sleeps.
      app.now = app.now.add(const Duration(minutes: 15, seconds: 5));
      await app.settle(2500);
      expect(app.location, '/rest');
      await flow.shot(device, '19_rest');
      await app.end();
    });
  }

  testWidgets('the youngest: three in a row, a change that sparkles, no two pictures, 小變 in front', (tester) async {
    final app = await TestApp.start(tester, game: const Game(settings: Settings(level: Level.small)));
    final flow = Flow(app);
    await app.tapLabel(Place.beach.zh, ms: 1200);
    expect(find.bySemanticsLabel(Mode.two.zh), findsNothing);
    await flow.shot('littlest', '01_place');

    await app.tapLabel(Mode.odd.zh, ms: 1500);
    final odd = flow.round as OddRound;
    expect(odd.count, 3);
    await flow.shot('littlest', '02_odd');
    await app.tapLabel(Strings.home, ms: 800);

    await app.tapLabel(Mode.change.zh, ms: 1500);
    final change = flow.round as ChangeRound;
    expect(change.diffs.single.thing.big, isTrue);
    await flow.wait(ChangeGame.lookFor(change).inMilliseconds / 1000 + ChangeGame.magic.inMilliseconds / 1000 + 0.6);
    expect(find.byType(Sparkles), findsWidgets, reason: 'the change sparkles for 2～3');
    await flow.shot('littlest', '03_change_sparkle');
    await flow.tapDiff(change.diffs.single);
    await app.tapLabel(Strings.home, ms: 800);

    await app.tapLabel(Mode.hide.zh, ms: 1500);
    final hide = flow.round as HideRound;
    expect(hide.onTop, isTrue);
    await flow.shot('littlest', '04_hide');
    await flow.tapBox(hide.box);
    await app.settle();
    await app.end();
  });

  testWidgets('every place and style draws; 20 seconds without a find brings a hint', (tester) async {
    final app = await TestApp.start(tester, game: const Game(settings: Settings(level: Level.big)));
    final flow = Flow(app);
    for (final p in Place.values) {
      app.go('/play/${p.name}/two');
      await app.settle(1500);
      final two = flow.round as TwoRound;
      expect(two.diffs, hasLength(5), reason: p.name);
      if (p == Place.park) {
        await flow.wait(21);
        expect(app.sounds.played.last, 'hint');
        expect(find.byType(HintGlow), findsWidgets);
      }
      await flow.shot('places', p.name);
    }
    await app.end();
  });
}

/// Steps through a game the way a child would, using the round on screen.
class Flow {
  Flow(this.app);

  final TestApp app;

  WidgetTester get tester => app.tester;

  Object get round => tester.state<PlayBoardState>(find.byType(PlayBoard)).debugRound;

  Future<void> shot(String device, String name) async {
    await app.settle(300);
    await shoot(tester, device, name);
  }

  Future<void> wait(double seconds) async {
    for (var i = 0; i < (seconds * 4).ceil(); i++) {
      await app.settle(250);
    }
  }

  /// Taps the picture [index] (0 the top one) at ([x], [y]), parts of its side.
  Future<void> tapAt(int index, double x, double y) async {
    final rect = tester.getRect(find.byType(SceneView).at(index));
    final side = rect.shortestSide;
    final topLeft = rect.center - Offset(side / 2, side / 2);
    await tester.tapAt(topLeft + Offset(x * side, y * side));
    await app.settle(500);
  }

  Future<void> tapBox(Box b, {int picture = 0}) => tapAt(picture, b.x, b.y);

  Future<void> tapDiff(Diff d, {int picture = 0}) => tapBox(d.box, picture: picture);

  Future<void> answerGate() async {
    const digits = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9};
    final parts = (find.textContaining('加').evaluate().first.widget as Text).data!.split(' ');
    for (final d in '${digits[parts[0]]! + digits[parts[2]]!}'.split('')) {
      await tester.tap(find.byKey(ValueKey('gate-key-$d')));
      await app.settle(200);
    }
    await app.settle(800);
  }
}
