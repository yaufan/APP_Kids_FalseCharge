import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/content.dart';
import '../core/providers.dart';
import '../features/album/album_screen.dart';
import '../features/home/home_screen.dart';
import '../features/home/place_screen.dart';
import '../features/parent/parent_gate.dart';
import '../features/parent/parent_screen.dart';
import '../features/play/play_screen.dart';
import '../features/rest/rest_screen.dart';
import 'strings.dart';
import 'theme.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final resting = ref.read(gameProvider).resting(ref.read(clockProvider)());
  final router = GoRouter(
    initialLocation: resting ? '/rest' : '/',
    // Always start here, whatever page another app asks the phone to open.
    overridePlatformDefaultLocation: true,
    redirect: (_, state) {
      final at = state.matchedLocation;
      if (at == '/parent' && !ParentPass.take()) return '/';
      final place = state.pathParameters['place'];
      if (place != null && Place.values.asNameMap()[place] == null) return '/';
      final mode = state.pathParameters['mode'];
      if (mode != null && Mode.values.asNameMap()[mode] == null) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, _) => const HomeScreen()),
      GoRoute(path: '/place/:place', builder: (_, s) => PlaceScreen(place: Place.values.byName(s.pathParameters['place']!))),
      GoRoute(
        path: '/play/:place/:mode',
        builder: (_, s) => PlayScreen(place: Place.values.byName(s.pathParameters['place']!), mode: Mode.values.byName(s.pathParameters['mode']!)),
      ),
      GoRoute(path: '/album', builder: (_, _) => const AlbumScreen()),
      GoRoute(path: '/rest', builder: (_, _) => const RestScreen()),
      GoRoute(path: '/parent', builder: (_, _) => const ParentScreen()),
    ],
  );
  ref.onDispose(router.dispose);
  return router;
});

class EyeApp extends ConsumerWidget {
  const EyeApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(gameProvider.select((g) => g.settings));
    ref.read(soundsProvider)
      ..music = settings.music
      ..effects = settings.sounds;
    return MaterialApp.router(
      title: Strings.appName,
      debugShowCheckedModeBanner: false,
      theme: EyeTheme.light(),
      locale: const Locale('zh', 'TW'),
      supportedLocales: const [Locale('zh', 'TW')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      routerConfig: ref.watch(routerProvider),
      builder: (_, child) => RestGuard(child: child ?? const SizedBox()),
    );
  }
}

/// Keeps the parent's play time: when the sitting has gone on for the
/// minutes they set, 小變 goes to sleep; an hour later (or when a parent says
/// so) play can go on. Away from the app for ten minutes counts as a rest.
class RestGuard extends ConsumerStatefulWidget {
  const RestGuard({super.key, required this.child});

  final Widget child;

  static const check = Duration(seconds: 2);
  static const awayIsRest = Duration(minutes: 10);

  @override
  ConsumerState<RestGuard> createState() => _RestGuardState();
}

class _RestGuardState extends ConsumerState<RestGuard> {
  Timer? _timer;
  AppLifecycleListener? _life;
  DateTime? _away;

  @override
  void initState() {
    super.initState();
    ref.read(sessionStartProvider);
    _timer = Timer.periodic(RestGuard.check, (_) => _check());
    _life = AppLifecycleListener(
      onHide: () => _away = ref.read(clockProvider)(),
      onShow: () {
        final away = _away;
        _away = null;
        if (away != null && ref.read(clockProvider)().difference(away) >= RestGuard.awayIsRest) ref.read(sessionStartProvider.notifier).restart();
        _check();
      },
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _life?.dispose();
    super.dispose();
  }

  void _check() {
    if (!mounted) return;
    final now = ref.read(clockProvider)();
    final g = ref.read(gameProvider);
    final router = ref.read(routerProvider);
    // The top page, including ones pushed on top (a deck, parent mode).
    final path = router.state.matchedLocation;
    if (path.startsWith('/parent')) return;
    if (g.restSince != null) {
      if (g.resting(now)) {
        if (path != '/rest') router.go('/rest');
        return;
      }
      ref.read(gameProvider.notifier).change((g) => g.playOn());
      ref.read(sessionStartProvider.notifier).restart();
      if (path == '/rest') router.go('/');
      return;
    }
    if (path == '/rest') return;
    if (now.difference(ref.read(sessionStartProvider)) >= Duration(minutes: g.settings.minutes)) {
      ref.read(gameProvider.notifier).change((g) => g.rest(now));
      router.go('/rest');
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
