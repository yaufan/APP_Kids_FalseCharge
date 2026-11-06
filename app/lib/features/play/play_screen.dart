import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/providers.dart';
import '../../core/puzzles.dart';
import '../../core/scenes.dart';
import '../../core/sounds.dart';
import 'change_game.dart';
import 'scene_view.dart';
import 'hide_game.dart';
import 'odd_game.dart';
import 'two_game.dart';

/// What a game tells the play screen.
class PlayHooks {
  const PlayHooks({required this.style, required this.line, required this.found, required this.miss, required this.sfx});

  /// The style the pictures are drawn in.
  final Style style;

  /// Show [text] in the bubble and say it.
  final void Function(String text) line;

  /// Something found; [last] ends the round.
  final void Function(String said, {required bool last}) found;

  /// A tap that found nothing, on the thing [id] if any (its name is said).
  final void Function(String? id) miss;
  final void Function(String sound) sfx;
}

/// One game in one place: a few rounds, then a star and the place in the
/// album (docs/design.md 「獎勵」). Never a fail: no clock, no score; a wrong
/// tap only makes a soft sound. 小變 gives a hint when asked, or (with many
/// hints) after a while without a find.
class PlayScreen extends ConsumerWidget {
  const PlayScreen({super.key, required this.place, required this.mode});

  final Place place;
  final Mode mode;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scene = ref.watch(sceneProvider(place));
    final look = ModeLook.of(mode);
    return Scaffold(
      body: Sky(
        top: look.top,
        bottom: look.bottom,
        child: scene.when(
          data: (s) => PlayBoard(key: ValueKey('${place.name}/${mode.name}'), scene: s, mode: mode),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (_, _) => Center(child: WideButton(label: Strings.toHome, icon: Icons.home_rounded, onTap: () => context.go('/'))),
        ),
      ),
    );
  }
}

class PlayBoard extends ConsumerStatefulWidget {
  const PlayBoard({super.key, required this.scene, required this.mode});

  final Scene scene;
  final Mode mode;

  /// Rounds in one game (two pictures is one big round).
  static int rounds(Mode m) => m == Mode.two ? 1 : 3;

  /// With many hints, 小變 shows where to look after this long without a find.
  static const autoHint = Duration(seconds: 20);

  @override
  ConsumerState<PlayBoard> createState() => PlayBoardState();
}

class PlayBoardState extends ConsumerState<PlayBoard> {
  late final Sounds _sounds;
  late final math.Random _random;
  late Object _round;
  var _roundNo = 0;
  var _done = 0;
  var _finished = false;
  var _cheer = false;
  var _hint = 0;
  String _line = '';
  Timer? _hintTimer, _wait, _cap, _next;
  Hide? _lastHide;

  Mode get _mode => widget.mode;
  Place get _place => widget.scene.place;

  /// The round on the screen (tests play it).
  @visibleForTesting
  Object get debugRound => _round;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _random = ref.read(randomProvider);
    _sounds.hold(this, Music.play);
    _sounds.play('amb_${_place.name}');
    _deal();
    WidgetsBinding.instance.addPostFrameCallback((_) => _ask());
  }

  @override
  void dispose() {
    for (final t in [_hintTimer, _wait, _cap, _next]) {
      t?.cancel();
    }
    _sounds.release(this);
    super.dispose();
  }

  void _deal() {
    final level = ref.read(gameProvider).settings.level;
    final s = widget.scene;
    final r = _random;
    _round = switch (_mode) {
      Mode.odd => OddRound.deal(s, level, r),
      Mode.change => ChangeRound.deal(s, level, r),
      // Two pictures starts at 3～4 (the parent may have set 2～3 meanwhile).
      Mode.two => TwoRound.deal(s, level == Level.small ? Level.mid : level, r),
      Mode.hide => HideRound.deal(s, level, r, not: _lastHide),
    };
    if (_round case HideRound h) _lastHide = h.hide;
    _cheer = false;
    _twoFound = 0;
    _roundNo++;
    _restartHintTimer();
  }

  /// The question of this round.
  String get _prompt => switch (_round) {
        OddRound r => Strings.oddAsk(r.lineup.zh),
        ChangeRound() => Strings.look,
        TwoRound r => Strings.twoAsk(r.diffs.length),
        _ => Strings.hideAsk,
      };

  /// Says [zh] (and [en] if the parent turned English on); completes when
  /// it has been said.
  Future<void> _say(String zh, {String? en}) async {
    final s = ref.read(gameProvider).settings;
    if (mounted && s.voice) await ref.read(voiceProvider).say(zh, en: s.english && en != null && en.isNotEmpty ? en : null);
  }

  void _ask() {
    if (!mounted) return;
    _setLine(_prompt);
  }

  void _setLine(String text) {
    if (!mounted) return;
    setState(() => _line = text);
    _say(text);
  }

  void _restartHintTimer() {
    _hintTimer?.cancel();
    if (_finished || !ref.read(gameProvider).settings.hints) return;
    _hintTimer = Timer(PlayBoard.autoHint, () => _giveHint(auto: true));
  }

  void _giveHint({bool auto = false}) {
    if (!mounted || _finished) return;
    _sounds.play('hint');
    setState(() => _hint++);
    _setLine(Strings.hint);
    _restartHintTimer();
  }

  void _found(String said, {required bool last}) {
    ref.read(gameProvider.notifier).change((g) => g.spotted(_place));
    _sounds.play('found');
    final praise = Strings.right[_random.nextInt(Strings.right.length)];
    final r = _round;
    final text = !last && r is TwoRound ? '$said${Strings.left(r.diffs.length - _twoFound)}' : '$praise$said';
    setState(() {
      _line = text;
      _cheer = true;
    });
    _restartHintTimer();
    if (!last) {
      _say(text);
      return;
    }
    _hintTimer?.cancel();
    if (_round is TwoRound) _sounds.play('all_found');
    // The next round comes once 小變 has finished talking (and at least a
    // moment to look), but never waits longer than [_longest].
    final round = _roundNo;
    var spoken = false, waited = false, gone = false;
    void go() {
      if (gone || !mounted || round != _roundNo || _finished) return;
      gone = true;
      _cap?.cancel();
      _next?.cancel();
      _next = Timer(const Duration(milliseconds: 600), _advance);
    }

    _say(text).then((_) {
      spoken = true;
      if (waited) go();
    });
    _wait?.cancel();
    _wait = Timer(_least, () {
      waited = true;
      if (spoken) go();
    });
    _cap?.cancel();
    _cap = Timer(_longest, go);
  }

  static const _least = Duration(milliseconds: 1800);
  static const _longest = Duration(seconds: 12);

  void _miss(String? id) {
    _sounds.play('miss');
    if (id == null) return;
    final t = widget.scene.thing(id);
    if (t != null) _say(t.zh, en: t.en);
  }

  void _advance() {
    if (!mounted) return;
    _done++;
    if (_done >= PlayBoard.rounds(_mode)) {
      ref.read(gameProvider.notifier).change((g) => g.finished(_place, _mode));
      _hintTimer?.cancel();
      _sounds.play('star');
      setState(() {
        _finished = true;
        _line = Strings.allFound;
      });
      _say('${Strings.allFound}${Strings.inAlbum(_place)}');
      return;
    }
    _sounds.play('next');
    setState(_deal);
    _ask();
  }

  void _again() {
    _sounds.play('next');
    setState(() {
      _finished = false;
      _done = 0;
      _deal();
    });
    _ask();
  }

  void _home() => context.canPop() ? context.pop() : context.go('/');

  Widget _board(PlayHooks hooks) {
    final key = ValueKey('round-$_roundNo');
    return switch (_round) {
      OddRound r => OddGame(key: key, round: r, hooks: hooks, hint: _hint),
      ChangeRound r => ChangeGame(key: key, round: r, hooks: hooks, hint: _hint),
      TwoRound r => TwoGame(key: key, round: r, hooks: hooks, hint: _hint),
      HideRound r => HideGame(key: key, round: r, hooks: hooks, hint: _hint),
      _ => const SizedBox(),
    };
  }

  /// Differences found so far in a two-pictures round.
  var _twoFound = 0;

  @override
  Widget build(BuildContext context) {
    final look = ModeLook.of(_mode);
    final style = ref.watch(gameProvider.select((g) => g.settings.style));
    final hooks = PlayHooks(
      style: style,
      line: _setLine,
      found: (said, {required last}) {
        if (_round is TwoRound) setState(() => _twoFound++);
        _found(said, last: last);
      },
      miss: _miss,
      sfx: _sounds.play,
    );
    final two = _round is TwoRound;
    return Stack(children: [
      SafeArea(
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
            child: Row(children: [
              RoundButton(label: Strings.home, icon: Icons.home_rounded, onTap: _home, size: 50),
              const SizedBox(width: 10),
              Expanded(
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: two
                      ? FoundDots(count: (_round as TwoRound).diffs.length, done: _twoFound, color: look.accent, size: 20)
                      : Pill(text: _mode.zh, color: look.accent),
                ),
              ),
              const SizedBox(width: 8),
              StyleSwitch(size: 50, onSwitched: (s) => _say(Strings.styleNow(s))),
            ]),
          ),
          if (!two)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 4),
              child: SpeakBubble(text: _line.isEmpty ? _prompt : _line, onTap: () => _say(_line.isEmpty ? _prompt : _line), color: look.accent),
            ),
          Expanded(child: Padding(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6), child: _finished ? const SizedBox() : _board(hooks))),
          SizedBox(
            height: two ? 72 : 96,
            child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
              const SizedBox(width: 8),
              Semantics(
                container: true,
                button: true,
                label: '小變',
                excludeSemantics: true,
                onTap: _ask,
                child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () {
                    _sounds.play('giggle');
                    _ask();
                  },
                  child: SizedBox.square(dimension: two ? 70 : 92, child: Chameleon(pose: _cheer ? 'cheer' : 'think', style: style)),
                ),
              ),
              if (two)
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(left: 6, bottom: 12),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: SpeakBubble(text: _line.isEmpty ? _prompt : _line, onTap: () => _say(_line.isEmpty ? _prompt : _line), size: 16, color: look.accent),
                    ),
                  ),
                )
              else
                const Spacer(),
              Padding(
                padding: const EdgeInsets.fromLTRB(8, 0, 14, 12),
                child: RoundButton(label: Strings.hint, icon: Icons.search_rounded, size: 58, sound: null, onTap: _finished ? null : _giveHint),
              ),
            ]),
          ),
        ]),
      ),
      if (_finished) Finished(scene: widget.scene, stars: ref.watch(gameProvider.select((g) => g.starsOf(_place))), style: style, onAgain: _again, onHome: _home),
    ]);
  }
}

/// A game played to the end: stars, the place's photo with 小變's stamp
/// going into the album, and play again or go home.
class Finished extends StatefulWidget {
  const Finished({super.key, required this.scene, required this.stars, required this.style, required this.onAgain, required this.onHome});

  final Scene scene;
  final int stars;
  final Style style;
  final VoidCallback onAgain;
  final VoidCallback onHome;

  @override
  State<Finished> createState() => _FinishedState();
}

class _FinishedState extends State<Finished> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400))..forward();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Positioned.fill(
        child: Container(
          decoration: const BoxDecoration(gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Color(0xFFFFF6E0), Color(0xFFFFE6EE)])),
          child: SafeArea(
            child: LayoutBuilder(builder: (context, box) {
              final photo = math.min(box.maxWidth * 0.6, box.maxHeight * 0.32);
              return Center(
                child: SingleChildScrollView(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                    ScaleTransition(
                      scale: CurvedAnimation(parent: _c, curve: const Interval(0, 0.5, curve: Curves.elasticOut)),
                      child: Stars(count: widget.stars, size: 54),
                    ),
                    const SizedBox(height: 6),
                    const Text(Strings.allFound, style: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: Eye.coral)),
                    const SizedBox(height: 14),
                    RotationTransition(
                      turns: Tween(begin: -0.02, end: -0.012).animate(_c),
                      child: Stack(clipBehavior: Clip.none, children: [
                        EyeCard(
                          radius: 14,
                          padding: const EdgeInsets.fromLTRB(10, 10, 10, 8),
                          child: SizedBox(
                            width: photo,
                            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            SceneView(picture: Picture.of(widget.scene), style: widget.style, side: photo, radius: 8),
                            const SizedBox(height: 6),
                            Row(children: [
                              Text(widget.scene.place.zh, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                              const SizedBox(width: 8),
                              Stars(count: widget.stars, size: 18),
                            ]),
                          ]),
                          ),
                        ),
                        Positioned(
                          right: -10,
                          bottom: 4,
                          child: ScaleTransition(
                            scale: CurvedAnimation(parent: _c, curve: const Interval(0.45, 0.8, curve: Curves.elasticOut)),
                            child: const Stamp(size: 84),
                          ),
                        ),
                      ]),
                    ),
                    const SizedBox(height: 8),
                    SizedBox.square(dimension: math.min(150, box.maxHeight * 0.18), child: Chameleon(pose: 'cheer', style: widget.style)),
                    const SizedBox(height: 10),
                    WideButton(label: Strings.next, icon: Icons.arrow_forward_rounded, onTap: widget.onAgain),
                    const SizedBox(height: 12),
                    WideButton(label: Strings.toHome, icon: Icons.home_rounded, color: Colors.white, onTap: widget.onHome),
                  ]),
                ),
              );
            }),
          ),
        ),
      );
}

/// 小變's red stamp: 「找到了」 in a round frame.
class Stamp extends StatelessWidget {
  const Stamp({super.key, this.size = 80});

  final double size;

  @override
  Widget build(BuildContext context) => Transform.rotate(
        angle: -0.25,
        child: Container(
          width: size,
          height: size,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white.withValues(alpha: 0.6),
            border: Border.all(color: Eye.coral, width: size * 0.05),
          ),
          child: Container(
            width: size * 0.8,
            height: size * 0.8,
            alignment: Alignment.center,
            decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: Eye.coral, width: size * 0.02)),
            child: Text(Strings.stamp, style: TextStyle(fontSize: size * 0.2, fontWeight: FontWeight.w700, color: Eye.coral)),
          ),
        ),
      );
}
