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
import '../../core/sounds.dart';
import '../play/scene_view.dart';

/// A place: its picture and the games to play there (three for 2～3, four
/// from 3～4), each a big button with its picture.
class PlaceScreen extends ConsumerStatefulWidget {
  const PlaceScreen({super.key, required this.place});

  final Place place;

  @override
  ConsumerState<PlaceScreen> createState() => _PlaceScreenState();
}

class _PlaceScreenState extends ConsumerState<PlaceScreen> {
  late final Sounds _sounds;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, Track(Music.home, widget.place));
    WidgetsBinding.instance.addPostFrameCallback((_) => _say(Strings.placeAsk(widget.place)));
  }

  @override
  void dispose() {
    _sounds.release(this);
    super.dispose();
  }

  void _say(String zh) {
    if (mounted && ref.read(gameProvider).settings.voice) ref.read(voiceProvider).say(zh);
  }

  void _play(Mode m) {
    _say(m.zh);
    context.push('/play/${widget.place.name}/${m.name}');
  }

  @override
  Widget build(BuildContext context) {
    final g = ref.watch(gameProvider);
    final style = g.settings.style;
    final scene = ref.watch(sceneProvider(widget.place)).value;
    final modes = [for (final m in Mode.values) if (g.settings.shows(m)) m];
    final done = g.done[widget.place] ?? const {};
    return Scaffold(
      body: Sky(
        top: Eye.sky,
        bottom: Eye.cream,
        child: SafeArea(
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: Row(children: [
                RoundButton(label: Strings.home, icon: Icons.home_rounded, size: 50, onTap: () => context.canPop() ? context.pop() : context.go('/')),
                const SizedBox(width: 10),
                Pill(text: widget.place.zh, color: placeColor(widget.place)),
                const SizedBox(width: 8),
                Stars(count: g.starsOf(widget.place), size: 22),
                const Spacer(),
                const StyleSwitch(size: 50),
              ]),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 6),
              child: SpeakBubble(text: Strings.placeAsk(widget.place), onTap: () => _say(Strings.placeAsk(widget.place)), size: 18),
            ),
            Expanded(
              flex: 5,
              child: Padding(
                padding: const EdgeInsets.all(10),
                child: scene == null ? const SizedBox() : SceneView(picture: Picture.of(scene), style: style),
              ),
            ),
            Expanded(
              flex: 4,
              child: LayoutBuilder(builder: (_, box) {
                const gap = 12.0;
                final w = math.min((box.maxWidth - 3 * gap) / 2, 260.0);
                final h = math.min((box.maxHeight - 3 * gap) / 2, w * 0.62);
                return Center(
                  child: Wrap(spacing: gap, runSpacing: gap, alignment: WrapAlignment.center, children: [
                    for (final m in modes) ModeButton(mode: m, width: w, height: h, done: done.contains(m), onTap: () => _play(m)),
                  ]),
                );
              }),
            ),
          ]),
        ),
      ),
    );
  }
}

/// A big button for a game: its colour, a picture of what it is, its name.
class ModeButton extends StatelessWidget {
  const ModeButton({super.key, required this.mode, required this.width, required this.height, required this.onTap, this.done = false});

  final Mode mode;
  final double width;
  final double height;
  final bool done;
  final VoidCallback onTap;

  static IconData icon(Mode m) => switch (m) {
        Mode.odd => Icons.grid_view_rounded,
        Mode.change => Icons.auto_fix_high_rounded,
        Mode.two => Icons.splitscreen_rounded,
        Mode.hide => Icons.visibility_rounded,
      };

  @override
  Widget build(BuildContext context) {
    final look = ModeLook.of(mode);
    return Semantics(
      container: true,
      button: true,
      label: mode.zh,
      excludeSemantics: true,
      onTap: onTap,
      child: Pressable(
        onTap: onTap,
        child: Container(
          width: width,
          height: height,
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
          decoration: BoxDecoration(
            color: look.accent,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [BoxShadow(color: Color.lerp(look.accent, Colors.black, 0.25)!, offset: const Offset(0, 5))],
          ),
          child: Stack(children: [
            Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(icon(mode), color: Colors.white, size: height * 0.38),
                const SizedBox(height: 4),
                FittedBox(child: Text(mode.zh, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700, color: Colors.white))),
              ]),
            ),
            if (done) const Positioned(right: 0, top: 0, child: Icon(Icons.star_rounded, color: Eye.gold, size: 26)),
          ]),
        ),
      ),
    );
  }
}
