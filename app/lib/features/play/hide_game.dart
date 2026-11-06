import 'package:flutter/material.dart';

import '../../app/strings.dart';
import '../../app/widgets.dart';
import '../../core/puzzles.dart';
import '../../core/scenes.dart';
import 'play_screen.dart';
import 'scene_view.dart';

/// 「小變躲在哪裡？」: 小變 has turned the colour of where he hides; only
/// his eyes and curly tail show. For 2～3 he sits in front and peeks out.
class HideGame extends StatefulWidget {
  const HideGame({super.key, required this.round, required this.hooks, required this.hint});

  final HideRound round;
  final PlayHooks hooks;
  final int hint;

  @override
  State<HideGame> createState() => HideGameState();
}

class HideGameState extends State<HideGame> {
  var found = false;
  /// The hint count when this round began (hints asked for before do not count).
  late final int _hintFrom;

  @override
  void initState() {
    super.initState();
    _hintFrom = widget.hint;
  }

  HideRound get _r => widget.round;

  void _touch(double x, double y) {
    if (found) return;
    if (_r.target.contains(x, y)) {
      setState(() => found = true);
      widget.hooks.sfx('giggle');
      widget.hooks.found(Strings.hideFound, last: true);
      return;
    }
    widget.hooks.miss(Puzzles.touched(_r.picture, x, y)?.id);
  }

  @override
  Widget build(BuildContext context) {
    final style = widget.hooks.style;
    final hiding = Art(chameleonPath(style, _r.art), fit: BoxFit.fill);
    final layers = <Layer>[
      if (!found) Layer(_r.box, _r.onTop ? Bob(amount: 2.5, child: hiding) : hiding, z: _r.onTop ? 1 << 20 : _r.hide.z, key: const ValueKey('hiding')),
      if (!found && widget.hint > _hintFrom) Layer(ringBox(_r.box).grown(pad: 0.05), const HintGlow(), key: const ValueKey('hint')),
      if (found) ...[
        Layer(ringBox(_r.box).grown(pad: 0.04), const Sparkles(count: 10), key: const ValueKey('burst')),
        Layer(_found(_r.box), Chameleon(pose: 'cheer', style: style), key: const ValueKey('found')),
        Layer(ringBox(_r.box), const FoundRing(), key: const ValueKey('ring')),
      ],
    ];
    return SceneView(picture: _r.picture, style: style, layers: layers, onTouch: _touch);
  }

  /// Where 小變 pops up when found: a little bigger, above his spot.
  Box _found(Box b) {
    final d = (b.w > b.h ? b.w : b.h) * 1.6;
    final s = d.clamp(0.16, 0.3);
    return Box(b.x.clamp(s / 2, 1 - s / 2), (b.y - s * 0.3).clamp(s / 2, 1 - s / 2), s, s);
  }
}
