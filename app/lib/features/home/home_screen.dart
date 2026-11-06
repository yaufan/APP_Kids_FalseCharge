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
import '../parent/parent_gate.dart';
import '../play/scene_view.dart';

/// The home page: 小變 says hello, the six places as cards with their
/// stars, the album, and (small, at the top) the way into parent mode.
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  late final Sounds _sounds;
  var _hello = 0;
  var _wiggle = 0;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, Music.home);
    if (ref.read(onceProvider).add('welcome')) WidgetsBinding.instance.addPostFrameCallback((_) => _say(Strings.welcome));
  }

  @override
  void dispose() {
    _sounds.release(this);
    super.dispose();
  }

  void _say(String zh, {String? en}) {
    final s = ref.read(gameProvider).settings;
    if (mounted && s.voice) ref.read(voiceProvider).say(zh, en: s.english ? en : null);
  }

  void _chameleon() {
    _sounds.play('giggle');
    setState(() {
      _wiggle++;
      _hello = (_hello + 1) % Strings.hello.length;
    });
    _say(Strings.hello[_hello]);
  }

  void _open(Place p) {
    if (!ref.read(gameProvider).settings.opens(p)) {
      _say(Strings.locked);
      return;
    }
    _say(p.zh, en: p.en);
    context.push('/place/${p.name}');
  }

  Future<void> _parent() async {
    if (await showParentGate(context) && mounted) await context.push('/parent');
  }

  @override
  Widget build(BuildContext context) {
    final style = ref.watch(gameProvider.select((g) => g.settings.style));
    return Scaffold(
      body: Sky(
        top: Eye.sky,
        bottom: Eye.cream,
        child: SafeArea(
          child: LayoutBuilder(builder: (context, box) {
            final wide = box.maxWidth > 600;
            final pad = box.maxWidth > 860 ? (box.maxWidth - 860) / 2 + 16 : 16.0;
            return Column(children: [
              Expanded(
                child: ListView(padding: EdgeInsets.fromLTRB(pad, 8, pad, 12), children: [
              Row(children: [
                const Spacer(),
                Semantics(
                  container: true,
                  button: true,
                  label: Strings.parent,
                  excludeSemantics: true,
                  onTap: _parent,
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: _parent,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.7), borderRadius: BorderRadius.circular(18)),
                      child: const Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.lock_outline_rounded, color: Eye.inkSoft, size: 18),
                        SizedBox(width: 4),
                        Text(Strings.parent, style: TextStyle(fontSize: 15, color: Eye.inkSoft)),
                      ]),
                    ),
                  ),
                ),
              ]),
              const SizedBox(height: 4),
              const Center(child: RainbowTitle(Strings.title, size: 34)),
              const SizedBox(height: 10),
              Row(children: [
                Semantics(
                  container: true,
                  button: true,
                  label: '小變',
                  excludeSemantics: true,
                  onTap: _chameleon,
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: _chameleon,
                    child: Wiggle(trigger: _wiggle, child: SizedBox.square(dimension: 118, child: Bob(child: Chameleon(pose: 'wave', style: style)))),
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(child: SpeakBubble(text: _hello == 0 ? Strings.welcome : Strings.hello[_hello], onTap: () => _say(_hello == 0 ? Strings.welcome : Strings.hello[_hello]), size: 18)),
              ]),
              const SizedBox(height: 14),
              GridView.count(
                crossAxisCount: wide ? 3 : 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 14,
                crossAxisSpacing: 14,
                childAspectRatio: 0.86,
                children: [for (final p in Place.values) PlaceCard(place: p, onTap: () => _open(p))],
              ),
                ]),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 6, 16, 14),
                child: WideButton(label: Strings.album, icon: Icons.photo_library_rounded, color: Eye.coral, onTap: () => context.push('/album')),
              ),
            ]);
          }),
        ),
      ),
    );
  }
}

/// A place: its picture, its name and stars (a lock while it is not open).
class PlaceCard extends ConsumerWidget {
  const PlaceCard({super.key, required this.place, required this.onTap});

  final Place place;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final g = ref.watch(gameProvider);
    final open = g.settings.opens(place);
    final scene = ref.watch(sceneProvider(place)).value;
    final style = g.settings.style;
    return Semantics(
      container: true,
      button: true,
      label: place.zh,
      excludeSemantics: true,
      onTap: onTap,
      child: Pressable(
        onTap: onTap,
        child: EyeCard(
          padding: const EdgeInsets.all(8),
          child: Column(children: [
            Expanded(
              child: LayoutBuilder(builder: (_, c) {
                final side = math.min(c.maxWidth, c.maxHeight);
                return Center(
                  child: Stack(children: [
                    scene == null
                        ? ClipRRect(borderRadius: BorderRadius.circular(14), child: SizedBox.square(dimension: side, child: Art(backgroundPath(style, place), fit: BoxFit.fill)))
                        : SceneView(picture: Picture.of(scene), style: style, side: side, radius: 14),
                    if (!open)
                      Positioned.fill(
                        child: Container(
                          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.55), borderRadius: BorderRadius.circular(14)),
                          child: const Icon(Icons.lock_rounded, size: 40, color: Eye.inkSoft),
                        ),
                      ),
                  ]),
                );
              }),
            ),
            const SizedBox(height: 6),
            Row(children: [
              Container(width: 10, height: 10, decoration: BoxDecoration(color: placeColor(place), shape: BoxShape.circle)),
              const SizedBox(width: 6),
              Expanded(child: Text(place.zh, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700))),
              Stars(count: g.starsOf(place), size: 17),
            ]),
          ]),
        ),
      ),
    );
  }
}

/// A title with each character in its own bright colour.
class RainbowTitle extends StatelessWidget {
  const RainbowTitle(this.text, {super.key, this.size = 32});

  final String text;
  final double size;

  static const _colors = [Color(0xFFF2665A), Color(0xFFFF8F3D), Color(0xFFF2B33B), Color(0xFF4CC46A), Color(0xFF3DB2E8), Color(0xFF6E7BE8), Color(0xFF9B7BE8)];

  @override
  Widget build(BuildContext context) {
    final chars = text.characters.toList();
    return Text.rich(
      TextSpan(children: [
        for (var i = 0; i < chars.length; i++)
          TextSpan(
            text: chars[i],
            style: TextStyle(color: _colors[i % _colors.length], shadows: const [Shadow(color: Colors.white, offset: Offset(0, 2.5))]),
          ),
      ]),
      semanticsLabel: text,
      style: TextStyle(fontSize: size, fontWeight: FontWeight.w700, letterSpacing: 2),
    );
  }
}
