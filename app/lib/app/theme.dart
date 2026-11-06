import 'package:flutter/material.dart';

import '../core/content.dart';

/// The app's colours (docs/mockups/): soft sky and cream pages, deep blue
/// words, 小變's green for what is found.
abstract final class Eye {
  static const ink = Color(0xFF33406B);
  static const inkSoft = Color(0xFF8A93B5);
  static const sky = Color(0xFFDDF0FF);
  static const cream = Color(0xFFFFF7EC);
  static const green = Color(0xFF4CC46A);
  static const orange = Color(0xFFFF8F3D);
  static const coral = Color(0xFFF2665A);
  static const purple = Color(0xFF9B7BE8);
  static const blue = Color(0xFF4C8DFF);
  static const gold = Color(0xFFFFC53D);
  static const glow = Color(0xFFFFE15A);
  static const card = Colors.white;
  static const edge = Color(0xFFD9DEEF);
  static const parentBg = Color(0xFFF3F4F9);
}

/// Each game's colour and its page's sky (the pill at the top, the dots).
class ModeLook {
  const ModeLook(this.accent, this.top, this.bottom);

  final Color accent;
  final Color top;
  final Color bottom;

  static ModeLook of(Mode m) => switch (m) {
        Mode.odd => const ModeLook(Eye.orange, Color(0xFFDDF0FF), Color(0xFFFFF1E2)),
        Mode.change => const ModeLook(Eye.green, Color(0xFFE2F6EA), Color(0xFFFFF7EC)),
        Mode.two => const ModeLook(Eye.blue, Color(0xFFE9E6FB), Color(0xFFF6F2FF)),
        Mode.hide => const ModeLook(Eye.purple, Color(0xFFEDE6FF), Color(0xFFFFF5E6)),
      };
}

/// Each place's colour (its card, its progress row).
Color placeColor(Place p) => switch (p) {
      Place.park => const Color(0xFF62C46A),
      Place.market => const Color(0xFF6E5BD6),
      Place.beach => const Color(0xFF3DB2E8),
      Place.zoo => const Color(0xFFF2A93B),
      Place.party => const Color(0xFFF27BA8),
      Place.kitchen => const Color(0xFFF28C3B),
    };

abstract final class EyeTheme {
  /// jf open 粉圓 (OFL): a rounded typeface made in Taiwan.
  static const font = 'Huninn';

  static ThemeData light() {
    final base = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: Eye.green, surface: Eye.cream),
      scaffoldBackgroundColor: Eye.cream,
      fontFamily: font,
      materialTapTargetSize: MaterialTapTargetSize.padded,
    );
    return base.copyWith(textTheme: base.textTheme.apply(bodyColor: Eye.ink, displayColor: Eye.ink, fontFamily: font));
  }
}
