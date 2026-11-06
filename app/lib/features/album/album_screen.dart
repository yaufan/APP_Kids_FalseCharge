import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/providers.dart';
import '../../core/scenes.dart';
import '../play/play_screen.dart';

/// The album: a photo of each place played to the end, with 小變's stamp
/// and its stars; empty frames for the ones still to visit.
class AlbumScreen extends ConsumerWidget {
  const AlbumScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final g = ref.watch(gameProvider);
    final style = g.settings.style;
    final have = Place.values.where(g.inAlbum).length;
    return Scaffold(
      body: Sky(
        top: const Color(0xFFFFEFE6),
        bottom: Eye.cream,
        child: SafeArea(
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: Row(children: [
                RoundButton(label: Strings.home, icon: Icons.home_rounded, size: 50, onTap: () => context.canPop() ? context.pop() : context.go('/')),
                const SizedBox(width: 10),
                const Pill(text: Strings.album, color: Eye.coral),
                const Spacer(),
                Text(Strings.albumCount(have, Place.values.length), style: const TextStyle(fontSize: 16, color: Eye.inkSoft, fontWeight: FontWeight.w700)),
              ]),
            ),
            Expanded(
              child: LayoutBuilder(builder: (_, box) {
                final cols = box.maxWidth > 600 ? 3 : 2;
                return GridView.count(
                  padding: const EdgeInsets.all(16),
                  crossAxisCount: cols,
                  mainAxisSpacing: 18,
                  crossAxisSpacing: 16,
                  childAspectRatio: 0.82,
                  children: [
                    for (final (i, p) in Place.values.indexed)
                      Transform.rotate(
                        angle: (i.isEven ? -1 : 1) * 0.025,
                        child: g.inAlbum(p) ? _Photo(place: p, style: style, stars: g.starsOf(p)) : _Empty(place: p),
                      ),
                  ],
                );
              }),
            ),
          ]),
        ),
      ),
    );
  }
}

class _Photo extends StatelessWidget {
  const _Photo({required this.place, required this.style, required this.stars});

  final Place place;
  final Style style;
  final int stars;

  @override
  Widget build(BuildContext context) => Semantics(
        label: '${place.zh}，$stars 顆星',
        child: Stack(clipBehavior: Clip.none, children: [
          EyeCard(
            radius: 10,
            padding: const EdgeInsets.fromLTRB(8, 8, 8, 6),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(child: ClipRRect(borderRadius: BorderRadius.circular(6), child: SizedBox.expand(child: Art(backgroundPath(style, place), fit: BoxFit.cover)))),
              const SizedBox(height: 4),
              Row(children: [
                Expanded(child: Text(place.zh, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700))),
                Stars(count: stars, size: 15),
              ]),
            ]),
          ),
          const Positioned(right: -8, bottom: 22, child: Stamp(size: 58)),
        ]),
      );
}

class _Empty extends StatelessWidget {
  const _Empty({required this.place});

  final Place place;

  @override
  Widget build(BuildContext context) => Semantics(
        label: '${place.zh}，${Strings.notYet}',
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Eye.edge, width: 2.5),
          ),
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            const Icon(Icons.help_outline_rounded, size: 44, color: Eye.edge),
            const SizedBox(height: 8),
            Text(place.zh, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: Eye.inkSoft)),
            const Text(Strings.notYet, style: TextStyle(fontSize: 14, color: Eye.inkSoft)),
          ]),
        ),
      );
}
