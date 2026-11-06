// Records a demo video of 眼尖尖大挑戰 being played: a scripted child (a
// white dot where the finger is) with a caption under the phone screen; the
// music and sounds the app asked for are written down and mixed in
// afterwards by tools/demo_audio.py.
//
//   flutter test test/demo/demo_video_test.dart --dart-define=DEMO=true
//   python3 ../tools/demo_audio.py
//
// Needs ffmpeg; writes build/demo/demo.mp4, chapters.txt and sounds.txt.
// Skipped in normal test runs.
import 'dart:io';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sharp_eyes/app/app.dart';
import 'package:sharp_eyes/app/strings.dart';
import 'package:sharp_eyes/core/content.dart';
import 'package:sharp_eyes/core/providers.dart';
import 'package:sharp_eyes/core/puzzles.dart';
import 'package:sharp_eyes/core/scenes.dart';
import 'package:sharp_eyes/core/sounds.dart';
import 'package:sharp_eyes/core/store.dart';
import 'package:sharp_eyes/core/voice.dart';
import 'package:sharp_eyes/features/play/change_game.dart';
import 'package:sharp_eyes/features/play/play_screen.dart';
import 'package:sharp_eyes/features/play/scene_view.dart';

import '../helpers.dart' show loadFonts;

const _phone = Size(390, 844);
const _captionHeight = 84.0;
const _fps = 10;
const _demo = bool.fromEnvironment('DEMO');

/// The music, the place's sounds and the short sounds asked for, with the
/// frame they were asked at.
class _Recording implements Sounds {
  _Recording(this.frame);

  final int Function() frame;
  final lines = <String>[];
  final _holders = TrackHolders();
  Track? _playing;

  @override
  set music(bool on) {}

  @override
  set effects(bool on) {}

  @override
  void play(String sfx) => lines.add('${frame()} sfx $sfx');

  @override
  void hold(Object owner, Track? track) {
    _holders.hold(owner, track);
    _changed();
  }

  @override
  void release(Object owner) {
    _holders.release(owner);
    _changed();
  }

  void _changed() {
    final now = _holders.current;
    if (now == _playing) return;
    if (now?.music != _playing?.music) lines.add('${frame()} music ${now?.music.file ?? '-'}');
    if (now?.ambience != _playing?.ambience) lines.add('${frame()} amb ${now?.ambience ?? '-'}');
    _playing = now;
  }
}

void main() {
  testWidgets('demo video', skip: !_demo, (tester) async {
    await tester.runAsync(loadFonts);
    tester.view.physicalSize = Size(_phone.width * 3, (_phone.height + _captionHeight) * 3);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);

    var frameCount = 0;
    var now = DateTime(2026, 11, 6, 10);
    final track = _Recording(() => frameCount);
    final finger = ValueNotifier<Offset?>(null);
    final caption = ValueNotifier<String>('');
    final key = GlobalKey();
    await tester.pumpWidget(RepaintBoundary(
      key: key,
      child: Directionality(
        textDirection: TextDirection.ltr,
        child: Column(children: [
          SizedBox.fromSize(
            size: _phone,
            child: MediaQuery(
              data: const MediaQueryData(size: _phone, devicePixelRatio: 3, padding: EdgeInsets.only(top: 24)),
              child: Stack(children: [
                ProviderScope(
                  overrides: [
                    storeProvider.overrideWithValue(MemoryStore()),
                    soundsProvider.overrideWithValue(track),
                    voiceProvider.overrideWithValue(const SilentVoice()),
                    randomProvider.overrideWithValue(math.Random(8)),
                    clockProvider.overrideWithValue(() => now),
                  ],
                  child: const EyeApp(),
                ),
                IgnorePointer(child: ValueListenableBuilder(valueListenable: finger, builder: (_, at, _) => _Finger(at))),
              ]),
            ),
          ),
          SizedBox(
            width: _phone.width,
            height: _captionHeight,
            child: ColoredBox(
              color: const Color(0xFF4CC46A),
              child: Center(
                child: ValueListenableBuilder(
                  valueListenable: caption,
                  builder: (_, text, _) => Text(text,
                      textAlign: TextAlign.center, style: const TextStyle(fontFamily: 'Huninn', color: Colors.white, fontSize: 17, height: 1.35)),
                ),
              ),
            ),
          ),
        ]),
      ),
    ));

    final rec = (await tester.runAsync(() => _Recorder.start(key)))!;
    final marks = <String>[];
    void mark(String name) => marks.add('$name $frameCount');
    Future<void> frames(int n) async {
      for (var i = 0; i < n; i++) {
        frameCount++;
        await tester.runAsync(() async {
          await rec.capture();
          await Future<void>.delayed(const Duration(milliseconds: 15));
        });
        await tester.pump(const Duration(milliseconds: 1000 ~/ _fps));
      }
    }

    Future<void> seconds(double s) => frames((s * _fps).round());
    Future<void> touch(Offset at) async {
      finger.value = at;
      await frames(2);
      await tester.tapAt(at);
      await frames(2);
      finger.value = null;
    }

    Offset at(String l) => tester.getCenter(find.bySemanticsLabel(l).last);
    Future<void> label(String l) => touch(at(l));
    Object round() => tester.state<PlayBoardState>(find.byType(PlayBoard)).debugRound;
    Offset onPicture(Box b, [int picture = 0]) {
      final rect = tester.getRect(find.byType(SceneView).at(picture));
      final side = rect.shortestSide;
      final topLeft = rect.center - Offset(side / 2, side / 2);
      return topLeft + Offset(b.x * side, b.y * side);
    }

    Future<void> open(Mode m) async {
      await label(m.zh);
      await seconds(2.2);
    }

    Future<void> home() async {
      await label(Strings.home);
      await seconds(1.2);
    }

    // Home.
    mark('home');
    caption.value = '眼尖尖大挑戰：調皮的變色龍「小變」\n偷偷把圖裡的東西變了，快來找一找！';
    await seconds(3.5);
    caption.value = '六個場景：公園、夜市、海邊\n動物園、生日派對、廚房';
    await seconds(2.5);
    await label(Place.park.zh);
    await seconds(2);
    caption.value = '四種玩法，2～5 歲分三個難度';
    await seconds(2);

    // 哪一個不一樣？ A whole game, to the album.
    mark('odd');
    caption.value = '「哪一個不一樣？」\n一排一樣的東西，找出不一樣的那一個';
    await open(Mode.odd);
    for (var r = 0; r < PlayBoard.rounds(Mode.odd); r++) {
      final odd = round() as OddRound;
      if (r == 0) {
        caption.value = '點錯只有輕輕的「噗」\n沒有倒數、沒有扣分';
        await touch(tester.getCenter(find.byKey(ValueKey('odd-${(odd.odd + 1) % odd.count}'))));
        await seconds(1.6);
        caption.value = '找到了，小變會說出哪裡不一樣';
      }
      await touch(tester.getCenter(find.byKey(ValueKey('odd-${odd.odd}'))));
      await seconds(r == 0 ? 3.6 : 3);
    }
    mark('album_stamp');
    caption.value = '玩完一種遊戲得一顆星\n照片蓋上小變的印章，放進相簿';
    await seconds(4);
    await label(Strings.toHome);
    await seconds(1.5);

    // 小變變了什麼？
    mark('change');
    caption.value = '「小變變了什麼？」\n先看一看，記住喔……';
    await open(Mode.change);
    final change = round() as ChangeRound;
    await seconds(ChangeGame.lookFor(change).inMilliseconds / 1000 - 2);
    caption.value = '小變說「變！」\n圖裡有東西變了';
    await seconds(ChangeGame.magic.inMilliseconds / 1000 + 1);
    for (final d in change.diffs) {
      await touch(onPicture(d.box));
      await seconds(2.4);
    }
    await seconds(1.5);
    await home();

    // 兩張找不同, and the three styles.
    mark('two');
    caption.value = '「兩張找不同」（3 歲以上）\n點上面或下面都可以，兩張都會圈起來';
    await open(Mode.two);
    final two = round() as TwoRound;
    for (final (i, d) in two.diffs.indexed) {
      await touch(onPicture(d.box, i.isEven ? 1 : 0));
      await seconds(2.2);
      if (i == 0) {
        mark('style');
        caption.value = '三種畫風隨時換，題目完全一樣';
        await label(Strings.switchStyle);
        caption.value = '孔版印刷風';
        await seconds(2.4);
        await label(Strings.switchStyle);
        caption.value = '粗蠟筆童畫風';
        await seconds(2.4);
        await label(Strings.switchStyle);
        caption.value = '等角小模型風（預設）';
        await seconds(1.6);
      }
    }
    await seconds(3);
    await label(Strings.toHome);
    await seconds(1.2);

    // 小變躲在哪裡？
    mark('hide');
    caption.value = '「小變躲在哪裡？」\n小變變色躲起來，只露出眼睛和捲尾巴';
    await open(Mode.hide);
    final hide = round() as HideRound;
    await seconds(1.5);
    caption.value = '找不到？點放大鏡，小變給提示';
    await label(Strings.hint);
    await seconds(2.5);
    await touch(onPicture(hide.box));
    await seconds(3);
    await home();
    await home();

    // The album.
    mark('album');
    caption.value = '相簿：玩過的場景都在這裡';
    await label(Strings.album);
    await seconds(3);
    await label(Strings.home);
    await seconds(1);

    // Time for a rest.
    mark('rest');
    now = now.add(const Duration(minutes: 15, seconds: 1));
    caption.value = '家長設定的時間到了（預設 15 分鐘）\n小變睡覺，眼睛也休息一下';
    await seconds(5.5);

    // Parent mode.
    mark('parent');
    caption.value = '家長答對題目，才能再玩或進家長模式';
    const digits = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9};
    Future<void> gate() async {
      final parts = (find.textContaining('加').evaluate().first.widget as Text).data!.split(' ');
      for (final d in '${digits[parts[0]]! + digits[parts[2]]!}'.split('')) {
        await touch(tester.getCenter(find.byKey(ValueKey('gate-key-$d'))));
        await frames(3);
      }
    }

    await label(Strings.parent);
    await seconds(1.2);
    await gate();
    await seconds(1.5);
    await label(Strings.parent);
    await seconds(1);
    await gate();
    await seconds(1);
    caption.value = '家長模式：年齡（三個難度）、每次玩多久\n一開始的畫風、提示多或少、聲音、英文';
    await seconds(3);
    await tester.drag(find.byType(ListView), const Offset(0, -900));
    await seconds(3);
    caption.value = '';
    mark('end');
    await seconds(0.5);

    await tester.runAsync(() async {
      await rec.finish();
      File('build/demo/chapters.txt').writeAsStringSync('${marks.join('\n')}\n');
      File('build/demo/sounds.txt').writeAsStringSync('fps $_fps\nframes $frameCount\n${track.lines.join('\n')}\n');
    });
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(milliseconds: 100));
  }, timeout: const Timeout(Duration(minutes: 40)));
}

class _Finger extends StatelessWidget {
  const _Finger(this.at);

  final Offset? at;

  @override
  Widget build(BuildContext context) {
    final p = at;
    if (p == null) return const SizedBox.expand();
    return Stack(children: [
      Positioned(
        left: p.dx - 22,
        top: p.dy - 22,
        child: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white.withValues(alpha: 0.55),
            border: Border.all(color: const Color(0xFF33406B).withValues(alpha: 0.5), width: 3),
          ),
        ),
      ),
    ]);
  }
}

/// Streams frames of [key]'s boundary into ffmpeg.
class _Recorder {
  _Recorder(this._key, this._ffmpeg);

  final GlobalKey _key;
  final Process _ffmpeg;

  static Future<_Recorder> start(GlobalKey key) async {
    Directory('build/demo').createSync(recursive: true);
    final size = Size(_phone.width * 2, (_phone.height + _captionHeight) * 2);
    final ffmpeg = await Process.start('ffmpeg', [
      '-y', '-loglevel', 'error',
      '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '${size.width.toInt()}x${size.height.toInt()}', '-r', '$_fps', '-i', '-',
      '-vf', 'fps=30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-movflags', '+faststart', 'build/demo/demo_silent.mp4',
    ]);
    ffmpeg.stderr.listen(stderr.add);
    return _Recorder(key, ffmpeg);
  }

  Future<void> capture() async {
    final boundary = _key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
    final image = await boundary.toImage(pixelRatio: 2);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
    image.dispose();
    _ffmpeg.stdin.add(bytes!.buffer.asUint8List());
    await _ffmpeg.stdin.flush();
  }

  Future<void> finish() async {
    await _ffmpeg.stdin.flush();
    await _ffmpeg.stdin.close();
    final code = await _ffmpeg.exitCode;
    if (code != 0) throw StateError('ffmpeg failed ($code)');
  }
}
