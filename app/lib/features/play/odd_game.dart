import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../app/widgets.dart';
import '../../core/puzzles.dart';
import '../../core/scenes.dart';
import 'play_screen.dart';
import 'scene_view.dart';

/// 「哪一個不一樣？」: the same thing three to five times, one of them
/// changed (a hat, another colour, turned round). Tap the different one.
class OddGame extends StatefulWidget {
  const OddGame({super.key, required this.round, required this.hooks, required this.hint});

  final OddRound round;
  final PlayHooks hooks;
  final int hint;

  @override
  State<OddGame> createState() => _OddGameState();
}

class _OddGameState extends State<OddGame> {
  var _found = false;
  final _wiggles = <int, int>{};
  late final int _hintFrom = widget.hint;

  OddRound get _r => widget.round;

  void _tap(int i) {
    if (_found) return;
    if (i == _r.odd) {
      setState(() => _found = true);
      widget.hooks.found(_r.said, last: true);
      return;
    }
    setState(() => _wiggles[i] = (_wiggles[i] ?? 0) + 1);
    widget.hooks.miss(null);
  }

  Widget _item(int i, double w) {
    final l = _r.lineup;
    final odd = i == _r.odd;
    final c = _r.change;
    final art = odd && c.kind == ChangeKind.art ? c.art! : l.art;
    final scale = odd && c.kind == ChangeKind.size ? c.scale : 1.0;
    final h = w * l.h / l.w;
    Widget picture = SizedBox(width: w * 0.8 * scale, height: h * 0.8 * scale, child: Art(artPath(widget.hooks.style, _r.scene.place, art), fit: BoxFit.contain));
    if (odd && c.kind == ChangeKind.flip) picture = Transform.flip(flipX: true, child: picture);
    final hinting = !_found && odd && widget.hint > _hintFrom;
    return Semantics(
      container: true,
      button: true,
      label: '${l.zh}${i + 1}',
      excludeSemantics: true,
      onTap: () => _tap(i),
      child: GestureDetector(
        key: ValueKey('odd-$i'),
        behavior: HitTestBehavior.opaque,
        onTapDown: (_) => _tap(i),
        child: Wiggle(
          trigger: _wiggles[i] ?? 0,
          child: SizedBox(
            width: w,
            height: h,
            child: Stack(clipBehavior: Clip.none, alignment: Alignment.center, children: [
              Positioned.fill(child: EyeCard(radius: w * 0.16, child: const SizedBox.expand())),
              if (hinting) const Positioned.fill(child: HintGlow()),
              Align(alignment: Alignment.bottomCenter, child: Padding(padding: EdgeInsets.only(bottom: h * 0.08), child: picture)),
              if (_found && odd) const Positioned.fill(child: FoundRing()),
            ]),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => LayoutBuilder(builder: (_, box) {
        final n = _r.count;
        // 3 in a row; 4 as two and two; 5 as three and two.
        final perRow = n == 4 ? 2 : 3;
        final rows = (n / perRow).ceil();
        final aspect = _r.lineup.h / _r.lineup.w;
        const gap = 14.0;
        final w = math.min((box.maxWidth - gap * (perRow + 1)) / perRow, (box.maxHeight - gap * (rows + 1)) / rows / aspect);
        return Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            for (var row = 0; row < rows; row++)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: gap / 2),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  for (var i = row * perRow; i < math.min(n, (row + 1) * perRow); i++) Padding(padding: const EdgeInsets.symmetric(horizontal: gap / 2), child: _item(i, w)),
                ]),
              ),
          ]),
        );
      });
}
