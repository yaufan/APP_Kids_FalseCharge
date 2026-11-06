import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/puzzles.dart';
import 'play_screen.dart';
import 'scene_view.dart';

/// 「兩張找不同」: the place twice, one above the other. A tap on either
/// picture counts; what is found is ringed in both.
class TwoGame extends StatefulWidget {
  const TwoGame({super.key, required this.round, required this.hooks, required this.hint});

  final TwoRound round;
  final PlayHooks hooks;
  final int hint;

  @override
  State<TwoGame> createState() => TwoGameState();
}

class TwoGameState extends State<TwoGame> {
  final found = <Diff>{};
  Diff? _hinted;
  /// The hint count when this round began (hints asked for before do not count).
  late final int _hintFrom;

  @override
  void initState() {
    super.initState();
    _hintFrom = widget.hint;
  }

  TwoRound get _r => widget.round;

  @override
  void didUpdateWidget(TwoGame oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.hint != oldWidget.hint && widget.hint > _hintFrom) {
      final left = _r.diffs.where((d) => !found.contains(d)).toList();
      if (left.isNotEmpty) setState(() => _hinted = left[widget.hint % left.length]);
    }
  }

  void _touch(Picture p, double x, double y) {
    if (found.length == _r.diffs.length) return;
    final d = Puzzles.hit(_r.diffs, x, y, found: found);
    if (d == null) {
      widget.hooks.miss(Puzzles.touched(p, x, y)?.id);
      return;
    }
    setState(() => found.add(d));
    widget.hooks.found(d.said, last: found.length == _r.diffs.length);
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (_, box) {
        const gap = 10.0;
        final side = math.min(box.maxWidth, (box.maxHeight - gap) / 2);
        final layers = foundLayers(found, hint: _hinted);
        return Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            SceneView(key: const ValueKey('top'), picture: _r.top, style: widget.hooks.style, side: side, layers: layers, onTouch: (x, y) => _touch(_r.top, x, y)),
            const SizedBox(height: gap),
            SceneView(key: const ValueKey('bottom'), picture: _r.bottom, style: widget.hooks.style, side: side, layers: layers, onTouch: (x, y) => _touch(_r.bottom, x, y)),
          ]),
        );
      });
}
