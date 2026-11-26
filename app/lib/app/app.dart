import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/content.dart';
import '../core/game.dart';
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

/// Keeps the parent's play time (docs/design.md 「每次玩多久」): when the
/// child has played the minutes they set, 小變 goes to sleep; an hour later
/// (or when a parent says so) play can go on.
///
/// Only play time counts: not the parent gate or parent mode, not the rest,
/// and not time with the app in the background (then it makes no checks and
/// never starts a rest). Away for ten minutes or more (in the background, or
/// closed: the sitting is kept in the save) is a new sitting. A phone clock
/// moved back gives no extra time and does not end a rest early.
class RestGuard extends ConsumerStatefulWidget {
  const RestGuard({super.key, required this.child});

  final Widget child;

  static const check = Duration(seconds: 2);

  /// Play time is saved this often (and when the app goes out of sight).
  static const saveEvery = Duration(seconds: 30);

  @override
  ConsumerState<RestGuard> createState() => _RestGuardState();
}

class _RestGuardState extends ConsumerState<RestGuard> {
  Timer? _timer;
  AppLifecycleListener? _life;
  late final GoRouter _router;

  /// When the app went out of sight (null: in sight).
  DateTime? _away;

  /// The clock when the time was last counted, and whether the time since
  /// then is play.
  late DateTime _last;
  var _counting = false;

  /// Play time not saved yet.
  var _unsaved = Duration.zero;

  /// How far the phone's clock was moved back (the rest moves with it).
  var _back = Duration.zero;

  /// Checks since the save was last written.
  var _sinceSave = 0;

  late final DateTime Function() _clock;

  DateTime get _now => _clock();

  String get _path => _router.routerDelegate.currentConfiguration.isEmpty ? '' : _router.state.matchedLocation;

  /// Whether the child is playing now: the app in sight, on a child's page,
  /// with no parent gate open.
  bool get _playing {
    final path = _path;
    return _away == null && path.isNotEmpty && !path.startsWith('/parent') && path != '/rest' && ParentGatePage.showing.value == 0;
  }

  @override
  void initState() {
    super.initState();
    _router = ref.read(routerProvider);
    _clock = ref.read(clockProvider);
    _last = _now;
    _router.routerDelegate.addListener(_count);
    ParentGatePage.showing.addListener(_count);
    _timer = Timer.periodic(RestGuard.check, (_) => _tick());
    _life = AppLifecycleListener(
      onHide: () {
        _count();
        _away = _now;
        _counting = false;
        _clockBack();
        _save(seen: true);
        // Nothing is said while the app is out of sight.
        ref.read(voiceProvider).stop();
      },
      onShow: () {
        _count();
        final away = _away;
        _away = null;
        if (away != null && _now.difference(away) >= Game.awayIsRest) {
          _unsaved = Duration.zero;
          ref.read(gameProvider.notifier).change((g) => g.newSitting(_now));
        }
        _counting = _playing;
        _check();
      },
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _life?.dispose();
    _router.routerDelegate.removeListener(_count);
    ParentGatePage.showing.removeListener(_count);
    super.dispose();
  }

  /// Counts the time since the last count (as play if it was), and looks at
  /// what the time from now on is. Called on every check and as soon as the
  /// page, the parent gate or the app being in sight changes (so it uses no
  /// providers: it may run while the pages are being taken down).
  void _count() {
    if (!mounted) return;
    final now = _now;
    final d = now.difference(_last);
    _last = now;
    if (d.isNegative) {
      _back -= d;
    } else if (_counting) {
      _unsaved += d;
    }
    _counting = _playing;
  }

  void _tick() {
    if (!mounted) return;
    _count();
    // Saved every half minute (when the app was last seen, too), and as
    // soon as the play stops.
    if (++_sinceSave * RestGuard.check.inSeconds >= RestGuard.saveEvery.inSeconds || (!_counting && _unsaved > Duration.zero)) _save(seen: _away == null);
    _check();
  }

  void _save({bool seen = false}) {
    if (_unsaved <= Duration.zero && !seen) return;
    final d = _unsaved, now = _now;
    _unsaved = Duration.zero;
    _sinceSave = 0;
    ref.read(gameProvider.notifier).change((g) => g.played(d, now));
  }

  /// A phone clock moved back: the rest (and when the app was last seen)
  /// move back with it.
  void _clockBack() {
    if (_back <= Duration.zero) return;
    final back = _back;
    _back = Duration.zero;
    ref.read(gameProvider.notifier).change((g) => g.clockBack(back));
  }

  void _check() {
    if (!mounted || _away != null) return;
    final now = _now;
    final game = ref.read(gameProvider.notifier);
    _clockBack();
    final g = ref.read(gameProvider);
    final path = _path;
    if (path.isEmpty || path.startsWith('/parent') || ParentGatePage.showing.value > 0) return;
    if (g.restSince != null) {
      if (g.resting(now)) {
        if (path != '/rest') _router.go('/rest');
        return;
      }
      _unsaved = Duration.zero;
      game.change((g) => g.playOn());
      if (path == '/rest') _router.go('/');
      return;
    }
    if (path == '/rest') {
      _router.go('/');
      return;
    }
    if (g.sitting.played + _unsaved >= Duration(minutes: g.settings.minutes)) {
      _unsaved = Duration.zero;
      game.change((g) => g.rest(now));
      _router.go('/rest');
    }
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
