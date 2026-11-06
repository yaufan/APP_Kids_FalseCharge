import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/puzzles.dart';
import '../../core/scenes.dart';

/// Something drawn on a picture besides its things: 小變 hiding (between the
/// things, by [z]), a found ring or a hint (on top).
class Layer {
  const Layer(this.box, this.child, {this.z = 1 << 20, this.key});

  final Box box;
  final Widget child;
  final int z;
  final Key? key;
}

/// A picture of a place in a style: the background, the things in z order
/// and the [layers], square, in a rounded frame. A finger on it reports
/// where, as parts of the side (0–1).
class SceneView extends StatelessWidget {
  const SceneView({super.key, required this.picture, required this.style, this.layers = const [], this.onTouch, this.side, this.radius = 22});

  final Picture picture;
  final Style style;
  final List<Layer> layers;
  final void Function(double x, double y)? onTouch;

  /// The size (the space given if not set).
  final double? side;
  final double radius;

  @override
  Widget build(BuildContext context) {
    Widget square(double s) {
      Widget at(Box b, Widget child, {Key? key}) => Positioned(key: key, left: b.left * s, top: b.top * s, width: b.w * s, height: b.h * s, child: child);
      final things = <(int, Widget)>[
        for (final p in picture.sprites)
          (
            p.z,
            at(
              p.box,
              key: ValueKey('${p.id}/${p.art}/${p.flip}'),
              p.flip ? Transform.flip(flipX: true, child: Art(artPath(style, picture.place, p.art), fit: BoxFit.fill)) : Art(artPath(style, picture.place, p.art), fit: BoxFit.fill),
            ),
          ),
        for (final l in layers) (l.z, at(l.box, l.child, key: l.key)),
      ];
      // A stable sort: things first, then the layers at the same height.
      final order = [for (var i = 0; i < things.length; i++) i]..sort((a, b) {
          final c = things[a].$1.compareTo(things[b].$1);
          return c != 0 ? c : a.compareTo(b);
        });
      final view = SizedBox(
        width: s,
        height: s,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(radius),
          child: Stack(clipBehavior: Clip.hardEdge, children: [
            Positioned.fill(child: Art(backgroundPath(style, picture.place), fit: BoxFit.fill)),
            for (final i in order) things[i].$2,
          ]),
        ),
      );
      final touch = onTouch;
      return Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(radius),
          boxShadow: const [BoxShadow(color: Color(0x335266A8), offset: Offset(0, 6), blurRadius: 14)],
        ),
        child: touch == null
            ? view
            : Listener(
                behavior: HitTestBehavior.opaque,
                onPointerDown: (e) => touch((e.localPosition.dx / s).clamp(0, 1), (e.localPosition.dy / s).clamp(0, 1)),
                child: view,
              ),
      );
    }

    final s = side;
    if (s != null) return square(s);
    return LayoutBuilder(builder: (_, c) => Center(child: square(math.min(c.maxWidth, c.maxHeight))));
  }
}

/// The green ring around something found (it pops in), with a tick.
class FoundRing extends StatefulWidget {
  const FoundRing({super.key, this.color = Eye.green});

  final Color color;

  @override
  State<FoundRing> createState() => _FoundRingState();
}

class _FoundRingState extends State<FoundRing> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 500))..forward();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ScaleTransition(
        scale: CurvedAnimation(parent: _c, curve: Curves.elasticOut),
        child: LayoutBuilder(builder: (_, c) {
          final d = math.min(c.maxWidth, c.maxHeight);
          return Stack(clipBehavior: Clip.none, children: [
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: math.max(3, d * 0.09)),
                ),
              ),
            ),
            Positioned.fill(
              child: Padding(
                padding: EdgeInsets.all(math.max(1, d * 0.02)),
                child: DecoratedBox(
                  decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: widget.color, width: math.max(2.5, d * 0.06))),
                ),
              ),
            ),
            Positioned(
              right: -d * 0.04,
              top: -d * 0.04,
              child: Container(
                width: math.max(16, d * 0.3),
                height: math.max(16, d * 0.3),
                decoration: BoxDecoration(color: widget.color, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 2)),
                child: Icon(Icons.check_rounded, color: Colors.white, size: math.max(12, d * 0.22)),
              ),
            ),
          ]);
        }),
      );
}

/// A soft yellow glow that pulses: 小變's hint.
class HintGlow extends StatefulWidget {
  const HintGlow({super.key});

  @override
  State<HintGlow> createState() => _HintGlowState();
}

class _HintGlowState extends State<HintGlow> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 900))..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => IgnorePointer(
        child: AnimatedBuilder(
          animation: _c,
          builder: (_, _) {
            final t = _c.value;
            return Stack(fit: StackFit.expand, children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(colors: [
                    Eye.glow.withValues(alpha: 0.5 + 0.3 * t),
                    Eye.glow.withValues(alpha: 0.3 + 0.2 * t),
                    Eye.glow.withValues(alpha: 0),
                  ], stops: const [0.25, 0.65, 1]),
                ),
              ),
              Transform.scale(
                scale: 0.82 + 0.12 * t,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFFFFB800).withValues(alpha: 0.6 + 0.4 * t), width: 4),
                  ),
                ),
              ),
            ]);
          },
        ),
      );
}

/// Sparkles bursting out once (小變's magic, a change that shows itself).
class Sparkles extends StatefulWidget {
  const Sparkles({super.key, this.count = 10, this.color = Eye.glow, this.repeat = false});

  final int count;
  final Color color;
  final bool repeat;

  @override
  State<Sparkles> createState() => _SparklesState();
}

class _SparklesState extends State<Sparkles> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 900));

  @override
  void initState() {
    super.initState();
    widget.repeat ? _c.repeat() : _c.forward();
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => IgnorePointer(
        child: AnimatedBuilder(
          animation: _c,
          builder: (_, _) => CustomPaint(painter: _SparklePainter(_c.value, widget.count, widget.color)),
        ),
      );
}

class _SparklePainter extends CustomPainter {
  _SparklePainter(this.t, this.count, this.color);

  final double t;
  final int count;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final c = size.center(Offset.zero);
    final reach = size.shortestSide * 0.62;
    final fade = t < 0.7 ? 1.0 : (1 - t) / 0.3;
    for (var i = 0; i < count; i++) {
      final a = i * 2 * math.pi / count + (i.isEven ? 0.2 : -0.1);
      final r = reach * (0.35 + 0.65 * Curves.easeOut.transform(t)) * (i.isEven ? 1 : 0.75);
      final p = c + Offset(math.cos(a), math.sin(a)) * r;
      final s = size.shortestSide * (i.isEven ? 0.09 : 0.06) * (1 - 0.4 * t);
      final star = Path();
      for (var k = 0; k < 8; k++) {
        final rr = k.isEven ? s : s * 0.38;
        final aa = -math.pi / 2 + k * math.pi / 4;
        final q = p + Offset(math.cos(aa), math.sin(aa)) * rr;
        k == 0 ? star.moveTo(q.dx, q.dy) : star.lineTo(q.dx, q.dy);
      }
      canvas.drawPath(star..close(), Paint()..color = (i % 3 == 0 ? Colors.white : color).withValues(alpha: fade.clamp(0, 1)));
    }
  }

  @override
  bool shouldRepaint(_SparklePainter old) => old.t != t;
}

/// A ring layer for each found difference, and the glow for a hint.
List<Layer> foundLayers(Iterable<Diff> found, {Diff? hint}) => [
      for (final d in found) Layer(ringBox(d.box), const FoundRing(), key: ValueKey('ring-${d.thing.id}')),
      if (hint != null && !found.contains(hint)) Layer(ringBox(hint.box).grown(pad: 0.03), const HintGlow(), key: const ValueKey('hint')),
    ];

/// A round box around [b], big enough to see.
Box ringBox(Box b) {
  final d = math.max(math.max(b.w, b.h) * 1.15, 0.12);
  return Box(b.x, b.y, d, d);
}
