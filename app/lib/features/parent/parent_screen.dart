import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/version.dart';
import '../../core/content.dart';
import '../../core/game.dart';
import '../../core/providers.dart';

/// Parent mode (after the gate): the child's age, play time, the style to
/// start in, hints, sounds, how each place is going and ideas for playing
/// together.
class ParentScreen extends ConsumerWidget {
  const ParentScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final g = ref.watch(gameProvider);
    final s = g.settings;
    final game = ref.read(gameProvider.notifier);
    final now = ref.read(clockProvider)();

    Widget section(String title, List<Widget> children) => Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Material(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 12),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: const TextStyle(fontSize: 15, color: Eye.inkSoft, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                ...children,
              ]),
            ),
          ),
        );

    Widget toggle(String label, bool value, void Function(bool)? set, {Key? key, String? note}) => SwitchListTile(
          key: key,
          contentPadding: EdgeInsets.zero,
          title: Text(label, style: const TextStyle(fontSize: 17)),
          subtitle: note == null ? null : Text(note, style: const TextStyle(fontSize: 13, color: Eye.inkSoft)),
          value: value,
          onChanged: set,
        );

    Widget chips<T>(List<T> values, T selected, String Function(T) label, void Function(T) pick, String keyOf) => Wrap(spacing: 8, runSpacing: 8, children: [
          for (final v in values)
            ChoiceChip(
              key: ValueKey('$keyOf-${v is Enum ? v.name : v}'),
              label: Text(label(v), style: const TextStyle(fontSize: 16)),
              selected: v == selected,
              onSelected: (_) => pick(v),
              selectedColor: const Color(0xFFD5F2DC),
              showCheckmark: false,
            ),
        ]);

    const note = TextStyle(fontSize: 14, height: 1.5, color: Eye.inkSoft);

    return Scaffold(
      backgroundColor: Eye.parentBg,
      appBar: AppBar(
        backgroundColor: Eye.parentBg,
        title: const Text(Strings.parentTitle),
        leading: IconButton(icon: const Icon(Icons.close_rounded), tooltip: Strings.back, onPressed: () => context.canPop() ? context.pop() : context.go('/')),
      ),
      body: ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
        section(Strings.age, [
          chips(Level.values, s.level, Strings.levelLine, (v) => game.settings((x) => x.copyWith(level: v)), 'level'),
          const SizedBox(height: 10),
          const Text(Strings.ageNote, style: note),
        ]),
        section(Strings.playTime, [
          chips(Settings.minuteChoices, s.minutes, Strings.minutes, (v) => game.settings((x) => x.copyWith(minutes: v)), 'minutes'),
          const SizedBox(height: 10),
          const Text(Strings.playTimeNote, style: note),
          if (g.resting(now)) ...[
            const SizedBox(height: 10),
            const Text(Strings.resting, style: TextStyle(fontSize: 16)),
            const SizedBox(height: 6),
            FilledButton(
              key: const ValueKey('play-on'),
              onPressed: () {
                game.change((g) => g.playOn());
                ref.read(sessionStartProvider.notifier).restart();
                context.go('/');
              },
              child: const Text(Strings.playOn),
            ),
          ],
        ]),
        section(Strings.style, [
          chips(Style.values, s.style, (v) => v.zh, (v) => game.settings((x) => x.copyWith(style: v)), 'style'),
          const SizedBox(height: 10),
          const Text(Strings.styleNote, style: note),
        ]),
        section(Strings.hints, [
          chips([true, false], s.hints, (v) => v ? Strings.hintsMany : Strings.hintsFew, (v) => game.settings((x) => x.copyWith(hints: v)), 'hints'),
          const SizedBox(height: 10),
          const Text(Strings.hintsNote, style: note),
        ]),
        section(Strings.sound, [
          toggle(Strings.music, s.music, (v) => game.settings((x) => x.copyWith(music: v)), key: const ValueKey('music')),
          toggle(Strings.effects, s.sounds, (v) => game.settings((x) => x.copyWith(sounds: v)), key: const ValueKey('effects')),
          toggle(Strings.voice, s.voice, (v) => game.settings((x) => x.copyWith(voice: v)), key: const ValueKey('voice')),
          toggle(Strings.english, s.english, (v) => game.settings((x) => x.copyWith(english: v)), key: const ValueKey('english')),
        ]),
        section(Strings.progress, [
          for (final p in Place.values)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(children: [
                Container(width: 12, height: 12, decoration: BoxDecoration(color: placeColor(p), borderRadius: BorderRadius.circular(3))),
                const SizedBox(width: 8),
                SizedBox(width: 76, child: Text(p.zh, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700))),
                Expanded(child: Text(Strings.progressLine(g.found[p] ?? 0, g.starsOf(p)), style: const TextStyle(fontSize: 15, color: Eye.inkSoft))),
                for (var i = 0; i < 3; i++) Icon(Icons.star_rounded, size: 18, color: i < g.starsOf(p) ? Eye.gold : const Color(0xFFE2E5F0)),
              ]),
            ),
          const SizedBox(height: 4),
          const Text(Strings.progressNote, style: note),
        ]),
        section(Strings.together, [
          for (final t in Strings.tips)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Padding(padding: EdgeInsets.only(top: 3), child: Icon(Icons.favorite_rounded, size: 16, color: Eye.coral)),
                const SizedBox(width: 8),
                Expanded(child: Text(t, style: const TextStyle(fontSize: 16, height: 1.45))),
              ]),
            ),
        ]),
        section(Strings.fullVersion, [
          const Text(Strings.fullNote, style: note),
          toggle(Strings.fullSwitch, s.full, (v) => game.settings((x) => x.copyWith(full: v)), key: const ValueKey('full')),
        ]),
        section(Strings.about, [
          const Text(Strings.privacy, style: TextStyle(fontSize: 15, height: 1.5)),
          const SizedBox(height: 6),
          Text(Strings.version(appVersion), style: note),
        ]),
      ]),
    );
  }
}
