import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/game.dart';
import '../../core/providers.dart';

/// A question a grown-up answers easily but a 2 to 5 year old cannot read:
/// the numbers are written out in Chinese characters (as in the sibling apps).
class ParentGateChallenge {
  ParentGateChallenge(this.a, this.b);

  factory ParentGateChallenge.random([math.Random? random]) {
    final r = random ?? math.Random();
    return ParentGateChallenge(3 + r.nextInt(7), 3 + r.nextInt(7));
  }

  final int a;
  final int b;

  static const _digits = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九'];

  String get question => Strings.gateQuestion(_digits[a], _digits[b]);

  int get answer => a + b;

  bool check(String typed) => int.tryParse(typed.trim()) == answer;
}

/// Completes with true only for a right answer. [forParentMode]: the
/// answer lets parent mode open (once); the rest screen only lets play go on.
Future<bool> showParentGate(BuildContext context, {bool forParentMode = true}) async {
  final ok = await Navigator.of(context).push<bool>(
    MaterialPageRoute(fullscreenDialog: true, builder: (_) => const ParentGatePage()),
  );
  if ((ok ?? false) && forParentMode) ParentPass.grant();
  return ok ?? false;
}

/// Parent mode opens only right after the gate was answered: the router
/// takes the pass, so nothing else (a link from another app) can open it.
abstract final class ParentPass {
  static var _open = false;

  static void grant() => _open = true;

  /// Whether parent mode may open now (once per right answer).
  static bool take() {
    final open = _open;
    _open = false;
    return open;
  }
}

/// Parent pages close by themselves when the app goes out of sight, or
/// after five minutes without a touch ([onLeave]), so a child who picks the
/// phone up again finds the child's pages, not parent mode; a pass from the
/// gate not used yet is used up.
class ParentGuard extends StatefulWidget {
  const ParentGuard({super.key, required this.onLeave, required this.child});

  final VoidCallback onLeave;
  final Widget child;

  static const idle = Duration(minutes: 5);

  @override
  State<ParentGuard> createState() => _ParentGuardState();
}

class _ParentGuardState extends State<ParentGuard> {
  Timer? _idle;
  AppLifecycleListener? _life;
  var _left = false;

  @override
  void initState() {
    super.initState();
    _life = AppLifecycleListener(onHide: _leave);
    _touched();
  }

  @override
  void dispose() {
    _idle?.cancel();
    _life?.dispose();
    super.dispose();
  }

  void _touched() {
    _idle?.cancel();
    _idle = Timer(ParentGuard.idle, _leave);
  }

  void _leave() {
    if (_left || !mounted) return;
    _left = true;
    _idle?.cancel();
    ParentPass.take();
    widget.onLeave();
  }

  @override
  Widget build(BuildContext context) => Listener(behavior: HitTestBehavior.translucent, onPointerDown: (_) => _touched(), child: widget.child);
}

/// Full screen, so a child cannot tap past it. Three wrong answers in a row
/// and it waits a minute, the next time five, then fifteen (GateLock, kept
/// in the save).
class ParentGatePage extends ConsumerStatefulWidget {
  const ParentGatePage({super.key, this.random});

  final math.Random? random;

  /// How many gates are open (the play time does not count meanwhile).
  static final showing = ValueNotifier<int>(0);

  @override
  ConsumerState<ParentGatePage> createState() => _ParentGatePageState();
}

class _ParentGatePageState extends ConsumerState<ParentGatePage> {
  late var _challenge = ParentGateChallenge.random(widget.random);
  var _typed = '';
  var _wrong = false;
  /// The wait was on screen when last drawn.
  var _shownLocked = false;
  Timer? _tick;

  DateTime get _now => ref.read(clockProvider)();

  @override
  void initState() {
    super.initState();
    ParentGatePage.showing.value++;
    _tick = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      // The seconds left count down, and the keys come back when it is over.
      if (_lock().locked(_now) || _shownLocked) setState(() {});
    });
  }

  @override
  void dispose() {
    _tick?.cancel();
    ParentGatePage.showing.value--;
    super.dispose();
  }

  /// The wait now (a clock moved back to before it began starts it again,
  /// saved).
  GateLock _lock() {
    final saved = ref.read(gameProvider).gate, lock = saved.checked(_now);
    if (!identical(lock, saved)) ref.read(gameProvider.notifier).change((g) => g.copyWith(gate: lock));
    return lock;
  }

  void _key(String k) {
    final now = _now;
    final lock = _lock();
    if (lock.locked(now)) return;
    setState(() {
      _wrong = false;
      if (k == '⌫') {
        if (_typed.isNotEmpty) _typed = _typed.substring(0, _typed.length - 1);
        return;
      }
      if (_typed.length >= 2) return;
      _typed += k;
    });
    if (_typed.length < '${_challenge.answer}'.length) return;
    final game = ref.read(gameProvider.notifier);
    if (_challenge.check(_typed)) {
      game.change((g) => g.copyWith(gate: const GateLock()));
      Navigator.of(context).pop(true);
      return;
    }
    game.change((g) => g.copyWith(gate: lock.miss(now)));
    setState(() {
      _wrong = true;
      _typed = '';
      _challenge = ParentGateChallenge.random(widget.random);
    });
  }

  @override
  Widget build(BuildContext context) {
    final now = _now;
    final lock = ref.watch(gameProvider.select((g) => g.gate)).checked(now);
    final locked = _shownLocked = lock.locked(now);
    final wait = locked ? lock.left(now) : Duration.zero;
    final need = '${_challenge.answer}'.length;
    Widget box(int i) => Container(
          width: 60,
          height: 70,
          margin: const EdgeInsets.only(right: 12),
          alignment: Alignment.center,
          decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), border: Border.all(color: i < _typed.length ? Eye.green : const Color(0xFFE2DDEB), width: 2.5)),
          child: Text(i < _typed.length ? _typed[i] : '', style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w700)),
        );
    Widget key(String k) => Semantics(
          key: ValueKey('gate-key-$k'),
          container: true,
          button: true,
          label: k == '⌫' ? Strings.backspace : k,
          excludeSemantics: true,
          child: Pressable(
            onTap: locked ? null : () => _key(k),
            child: Container(
              height: 64,
              alignment: Alignment.center,
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18), border: Border.all(color: const Color(0xFFE2DDEB))),
              child: k == '⌫' ? const Icon(Icons.backspace_outlined, color: Eye.inkSoft) : Text(k, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700)),
            ),
          ),
        );
    return ParentGuard(
      onLeave: () => Navigator.of(context).pop(false),
      child: Scaffold(
      backgroundColor: Eye.parentBg,
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: ListView(padding: const EdgeInsets.all(20), children: [
              Row(children: [
                const Expanded(
                  child: EyeCard(
                    padding: EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                    child: Text(Strings.callParent, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
                  ),
                ),
                const SizedBox(width: 8),
                RoundButton(label: Strings.cancel, icon: Icons.close_rounded, onTap: () => Navigator.of(context).pop(false)),
              ]),
              const SizedBox(height: 18),
              Container(
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24)),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Row(children: [
                    Icon(Icons.lock_outline_rounded, size: 18, color: Eye.inkSoft),
                    SizedBox(width: 8),
                    Text(Strings.parentGateTitle, style: TextStyle(fontSize: 15, color: Eye.inkSoft)),
                  ]),
                  const SizedBox(height: 10),
                  Text(locked ? Strings.gateWait(wait) : _challenge.question, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 18),
                  if (!locked) Row(children: [for (var i = 0; i < need; i++) box(i)]),
                  const SizedBox(height: 14),
                  Text(_wrong ? Strings.wrongAnswer : Strings.gateRules, style: TextStyle(fontSize: 14, color: _wrong ? const Color(0xFFD9655A) : Eye.inkSoft)),
                ]),
              ),
              const SizedBox(height: 22),
              GridView.count(
                crossAxisCount: 3,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.7,
                children: [
                  for (final k in ['1', '2', '3', '4', '5', '6', '7', '8', '9']) key(k),
                  const SizedBox.shrink(),
                  key('0'),
                  key('⌫'),
                ],
              ),
            ]),
          ),
        ),
      ),
      ),
    );
  }
}
