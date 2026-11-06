import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../core/content.dart';
import '../core/providers.dart';
import '../core/scenes.dart';
import 'strings.dart';
import 'theme.dart';

/// A drawing from assets/art/ (nothing at all if it is missing).
class Art extends StatelessWidget {
  const Art(this.path, {super.key, this.fit = BoxFit.contain});

  final String path;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) => SvgPicture.asset(
        path,
        fit: fit,
        excludeFromSemantics: true,
        errorBuilder: (_, _, _) => const SizedBox.expand(),
      );
}

/// 小變 in the style being played: wave, think, cheer or magic.
class Chameleon extends ConsumerWidget {
  const Chameleon({super.key, this.pose = 'wave', this.style});

  final String pose;

  /// The parent's style if not given.
  final Style? style;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final Style s = style ?? ref.watch(gameProvider.select((g) => g.settings.style));
    return Art(chameleonPath(s, pose));
  }
}

/// Shrinks a little while pressed and clicks.
class Pressable extends ConsumerStatefulWidget {
  const Pressable({super.key, required this.child, this.onTap, this.sound = 'tap'});

  final Widget child;
  final VoidCallback? onTap;
  final String? sound;

  @override
  ConsumerState<Pressable> createState() => _PressableState();
}

class _PressableState extends ConsumerState<Pressable> {
  var _down = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onTap != null;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      excludeFromSemantics: true,
      onTapDown: enabled ? (_) => setState(() => _down = true) : null,
      onTapCancel: enabled ? () => setState(() => _down = false) : null,
      onTapUp: enabled ? (_) => setState(() => _down = false) : null,
      onTap: enabled
          ? () {
              final s = widget.sound;
              if (s != null) ref.read(soundsProvider).play(s);
              widget.onTap!();
            }
          : null,
      child: AnimatedScale(scale: _down ? 0.93 : 1, duration: const Duration(milliseconds: 90), child: widget.child),
    );
  }
}

/// A white card with a soft blue edge under it.
class EyeCard extends StatelessWidget {
  const EyeCard({super.key, this.child, this.padding = EdgeInsets.zero, this.color = Eye.card, this.ring, this.radius = 22});

  final Widget? child;
  final EdgeInsets padding;
  final Color color;
  final Color? ring;
  final double radius;

  @override
  Widget build(BuildContext context) => AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: padding,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(radius),
          border: ring == null ? null : Border.all(color: ring!, width: 4),
          boxShadow: const [BoxShadow(color: Color(0x2E5266A8), offset: Offset(0, 5), blurRadius: 12)],
        ),
        child: child,
      );
}

/// A round button with an icon.
class RoundButton extends StatelessWidget {
  const RoundButton({super.key, required this.label, required this.icon, this.onTap, this.size = 54, this.color, this.sound = 'tap', this.child});

  final String label;
  final IconData icon;
  final VoidCallback? onTap;
  final double size;

  /// Filled with this colour (white if not).
  final Color? color;
  final String? sound;

  /// Drawn instead of the icon.
  final Widget? child;

  @override
  Widget build(BuildContext context) => Semantics(
        container: true,
        button: true,
        label: label,
        excludeSemantics: true,
        onTap: onTap,
        child: Pressable(
          onTap: onTap,
          sound: sound,
          child: Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              color: color ?? Colors.white,
              shape: BoxShape.circle,
              boxShadow: const [BoxShadow(color: Color(0x335266A8), offset: Offset(0, 4), blurRadius: 8)],
            ),
            child: child ?? Icon(icon, size: size * 0.52, color: color == null ? Eye.ink : Colors.white),
          ),
        ),
      );
}

/// A wide button with an icon and a word.
class WideButton extends StatelessWidget {
  const WideButton({super.key, required this.label, required this.icon, this.onTap, this.color = Eye.green, this.height = 62, this.sound = 'tap'});

  final String label;
  final IconData icon;
  final VoidCallback? onTap;
  final Color color;
  final double height;
  final String? sound;

  @override
  Widget build(BuildContext context) {
    final light = color == Colors.white;
    return Semantics(
      container: true,
      button: true,
      label: label,
      excludeSemantics: true,
      onTap: onTap,
      child: Pressable(
        onTap: onTap,
        sound: sound,
        child: Container(
          height: height,
          padding: EdgeInsets.symmetric(horizontal: height * 0.45),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(height / 2),
            boxShadow: [BoxShadow(color: light ? const Color(0x335266A8) : Color.lerp(color, Colors.black, 0.25)!, offset: const Offset(0, 5))],
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: height * 0.46, color: light ? Eye.green : Colors.white),
            const SizedBox(width: 10),
            Text(label, style: TextStyle(fontSize: height * 0.36, fontWeight: FontWeight.w700, color: light ? Eye.ink : Colors.white)),
          ]),
        ),
      ),
    );
  }
}

/// A pill with a game's name.
class Pill extends StatelessWidget {
  const Pill({super.key, required this.text, required this.color, this.size = 19});

  final String text;
  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        padding: EdgeInsets.symmetric(horizontal: size * 0.95, vertical: size * 0.32),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(size * 2),
          boxShadow: [BoxShadow(color: Color.lerp(color, Colors.black, 0.2)!, offset: const Offset(0, 3))],
        ),
        child: Text(text, maxLines: 1, overflow: TextOverflow.fade, softWrap: false, style: TextStyle(fontSize: size, fontWeight: FontWeight.w700, color: Colors.white)),
      );
}

/// A speech bubble with a speaker: tap to hear it again.
class SpeakBubble extends StatelessWidget {
  const SpeakBubble({super.key, required this.text, this.onTap, this.size = 20, this.color = Eye.green});

  final String text;
  final VoidCallback? onTap;
  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) => Semantics(
        container: true,
        button: onTap != null,
        label: text,
        excludeSemantics: true,
        onTap: onTap,
        child: Pressable(
          onTap: onTap,
          sound: null,
          child: EyeCard(
            radius: 26,
            padding: const EdgeInsets.fromLTRB(10, 8, 18, 8),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              Container(
                width: size * 1.7,
                height: size * 1.7,
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
                child: Icon(Icons.volume_up_rounded, color: Colors.white, size: size),
              ),
              const SizedBox(width: 10),
              Flexible(child: Text(text, style: TextStyle(fontSize: size, fontWeight: FontWeight.w700, color: Eye.ink, height: 1.3))),
            ]),
          ),
        ),
      );
}

/// Switches the drawing style (the same puzzle, drawn another way).
class StyleSwitch extends ConsumerWidget {
  const StyleSwitch({super.key, this.size = 52, this.onSwitched});

  final double size;
  final void Function(Style now)? onSwitched;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final style = ref.watch(gameProvider.select((g) => g.settings.style));
    return RoundButton(
      label: Strings.switchStyle,
      icon: Icons.palette_rounded,
      size: size,
      sound: 'switch_style',
      onTap: () {
        final next = style.next;
        ref.read(gameProvider.notifier).settings((s) => s.copyWith(style: next));
        onSwitched?.call(next);
      },
      child: Padding(
        padding: EdgeInsets.all(size * 0.08),
        child: Stack(children: [
          Positioned.fill(child: ClipOval(child: Chameleon(pose: 'wave', style: style.next))),
          Positioned(
            right: 0,
            bottom: 0,
            child: Container(
              width: size * 0.36,
              height: size * 0.36,
              decoration: const BoxDecoration(color: Eye.purple, shape: BoxShape.circle),
              child: Icon(Icons.autorenew_rounded, size: size * 0.26, color: Colors.white),
            ),
          ),
        ]),
      ),
    );
  }
}

/// Shakes its child side to side once each time [trigger] changes.
class Wiggle extends StatefulWidget {
  const Wiggle({super.key, required this.trigger, required this.child, this.amount = 0.08});

  final int trigger;
  final Widget child;
  final double amount;

  @override
  State<Wiggle> createState() => _WiggleState();
}

class _WiggleState extends State<Wiggle> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));

  @override
  void didUpdateWidget(Wiggle old) {
    super.didUpdateWidget(old);
    if (old.trigger != widget.trigger) _c.forward(from: 0);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _c,
        builder: (_, child) {
          final t = _c.value;
          return Transform.rotate(angle: math.sin(t * math.pi * 4) * (1 - t) * widget.amount, child: child);
        },
        child: widget.child,
      );
}

/// A gentle bob up and down.
class Bob extends StatefulWidget {
  const Bob({super.key, required this.child, this.phase = 0, this.amount = 4});

  final Widget child;
  final double phase;
  final double amount;

  @override
  State<Bob> createState() => _BobState();
}

class _BobState extends State<Bob> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1800))..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _c,
        builder: (_, child) => Transform.translate(offset: Offset(0, math.sin((_c.value + widget.phase) * 2 * math.pi) * widget.amount), child: child),
        child: widget.child,
      );
}

/// Dots: [done] of [count] filled (found ones get a tick).
class FoundDots extends StatelessWidget {
  const FoundDots({super.key, required this.count, required this.done, this.color = Eye.green, this.size = 22});

  final int count;
  final int done;
  final Color color;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(size)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          for (var i = 0; i < count; i++)
            AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              margin: const EdgeInsets.symmetric(horizontal: 2.5),
              width: size,
              height: size,
              decoration: BoxDecoration(color: i < done ? color : const Color(0xFFE4E7F2), shape: BoxShape.circle),
              child: i < done ? Icon(Icons.check_rounded, size: size * 0.75, color: Colors.white) : null,
            ),
        ]),
      );
}

/// Up to three stars.
class Stars extends StatelessWidget {
  const Stars({super.key, required this.count, this.size = 18});

  final int count;
  final double size;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        for (var i = 0; i < 3; i++) Icon(Icons.star_rounded, size: size, color: i < count ? Eye.gold : const Color(0xFFE2E5F0)),
      ]);
}

/// The page's soft sky.
class Sky extends StatelessWidget {
  const Sky({super.key, required this.top, required this.bottom, required this.child});

  final Color top;
  final Color bottom;
  final Widget child;

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [top, bottom])),
        child: child,
      );
}
