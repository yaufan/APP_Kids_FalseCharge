import 'dart:async';

import 'package:flutter/material.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/puzzles.dart';
import 'play_screen.dart';
import 'scene_view.dart';

/// 「小變變了什麼？」: look at the place, 小變 says 「變！」 with a burst of
/// sparkles, and something is different. For 2～3 the change sparkles as
/// it happens; older children remember (and may peek at how it was).
class ChangeGame extends StatefulWidget {
  const ChangeGame({super.key, required this.round, required this.hooks, required this.hint});

  final ChangeRound round;
  final PlayHooks hooks;
  final int hint;

  /// How long to look before the magic.
  static Duration lookFor(ChangeRound r) => Duration(milliseconds: r.flash ? 3500 : 5000);

  /// How long the burst of magic takes.
  static const magic = Duration(milliseconds: 1100);

  @override
  State<ChangeGame> createState() => ChangeGameState();
}

enum ChangeStep { look, magic, find }

class ChangeGameState extends State<ChangeGame> {
  var step = ChangeStep.look;
  final found = <Diff>{};
  var _peek = false;
  Diff? _hinted;
  /// The hint count when this round began (hints asked for before do not count).
  late final int _hintFrom;
  Timer? _timer, _peekTimer;

  ChangeRound get _r => widget.round;

  @override
  void initState() {
    super.initState();
    _hintFrom = widget.hint;
    _timer = Timer(ChangeGame.lookFor(_r), _magic);
  }

  @override
  void didUpdateWidget(ChangeGame oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.hint != oldWidget.hint && widget.hint > _hintFrom) {
      // A hint while still looking: do the magic now.
      if (step == ChangeStep.look) {
        _timer?.cancel();
        _magic();
      }
      setState(() => _hinted = _r.diffs.where((d) => !found.contains(d)).firstOrNull);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _peekTimer?.cancel();
    super.dispose();
  }

  void _magic() {
    if (!mounted || step != ChangeStep.look) return;
    widget.hooks.sfx('magic');
    widget.hooks.line(Strings.magic);
    setState(() => step = ChangeStep.magic);
    _timer = Timer(ChangeGame.magic, () {
      if (!mounted) return;
      setState(() => step = ChangeStep.find);
      widget.hooks.line(_r.diffs.length == 1 ? Strings.changedOne : Strings.changedTwo);
    });
  }

  void _touch(double x, double y) {
    if (step == ChangeStep.look) {
      final s = Puzzles.touched(_r.before, x, y);
      if (s != null) widget.hooks.miss(s.id);
      return;
    }
    if (step != ChangeStep.find || found.length == _r.diffs.length) return;
    final d = Puzzles.hit(_r.diffs, x, y, found: found);
    if (d == null) {
      widget.hooks.miss(Puzzles.touched(_r.after, x, y)?.id);
      return;
    }
    setState(() => found.add(d));
    widget.hooks.found(d.said, last: found.length == _r.diffs.length);
  }

  void _peekNow() {
    widget.hooks.sfx('peek');
    setState(() => _peek = true);
    _peekTimer?.cancel();
    _peekTimer = Timer(const Duration(milliseconds: 1600), () {
      if (mounted) setState(() => _peek = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final showBefore = step == ChangeStep.look || (_peek && step == ChangeStep.find);
    final layers = <Layer>[
      if (step == ChangeStep.find && !_peek) ...foundLayers(found, hint: _hinted),
      if (step == ChangeStep.find && _r.flash)
        for (final d in _r.diffs)
          if (!found.contains(d)) Layer(ringBox(d.box).grown(pad: 0.04), const Sparkles(count: 8), key: ValueKey('flash-${d.thing.id}')),
    ];
    return Column(children: [
      Expanded(
        child: Stack(alignment: Alignment.center, children: [
          SceneView(picture: showBefore ? _r.before : _r.after, style: widget.hooks.style, layers: layers, onTouch: _touch),
          if (step == ChangeStep.magic)
            Positioned.fill(
              child: IgnorePointer(
                child: Center(
                  child: FractionallySizedBox(
                    widthFactor: 0.9,
                    heightFactor: 0.9,
                    child: Stack(alignment: Alignment.center, children: [
                      const Positioned.fill(child: Sparkles(count: 14)),
                      FractionallySizedBox(widthFactor: 0.45, heightFactor: 0.45, child: Chameleon(pose: 'magic', style: widget.hooks.style)),
                    ]),
                  ),
                ),
              ),
            ),
          if (_peek && step == ChangeStep.find)
            Positioned(
              top: 10,
              child: Pill(text: Strings.peek, color: Eye.inkSoft, size: 15),
            ),
        ]),
      ),
      if (!_r.flash && step == ChangeStep.find)
        Padding(
          padding: const EdgeInsets.only(top: 8),
          child: RoundButton(label: Strings.peek, icon: Icons.visibility_rounded, size: 48, onTap: _peekNow, sound: null),
        ),
    ]);
  }
}
