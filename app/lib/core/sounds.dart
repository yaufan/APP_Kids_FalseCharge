import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/widgets.dart';

import 'content.dart';

/// The music (design/sounds/make_sounds.py): the home page, playing, and
/// the quiet one for resting.
enum Music {
  home('music_home'),
  play('music_play'),
  rest('music_rest');

  const Music(this.file);

  final String file;
}

/// What a screen wants to hear: a tune, and (in a place) its sounds — birds
/// in the park, waves at the beach.
class Track {
  const Track(this.music, [this.place]);

  final Music music;
  final Place? place;

  String? get ambience => place == null ? null : 'amb_${place!.name}';

  @override
  bool operator ==(Object other) => other is Track && other.music == music && other.place == place;

  @override
  int get hashCode => Object.hash(music, place);
}

/// Short sounds are named by their file in assets/sounds/ (tap, found, miss…).
abstract interface class Sounds {
  set music(bool on);
  set effects(bool on);

  void play(String sfx);

  /// [owner] (a screen) wants [track]; the one asked for last plays.
  void hold(Object owner, Track? track);

  void release(Object owner);
}

class TrackHolders {
  final _holders = <Object, Track?>{};

  void hold(Object owner, Track? track) {
    _holders.remove(owner);
    _holders[owner] = track;
  }

  void release(Object owner) => _holders.remove(owner);

  Track? get current => _holders.isEmpty ? null : _holders.values.last;
}

class SilentSounds implements Sounds {
  const SilentSounds();

  @override
  set music(bool on) {}

  @override
  set effects(bool on) {}

  @override
  void play(String sfx) {}

  @override
  void hold(Object owner, Track? track) {}

  @override
  void release(Object owner) {}
}

/// Remembers the sounds played (tests).
class RecordingSounds implements Sounds {
  final played = <String>[];
  final _holders = TrackHolders();

  Track? get track => _holders.current;

  @override
  set music(bool on) {}

  @override
  set effects(bool on) {}

  @override
  void play(String sfx) => played.add(sfx);

  @override
  void hold(Object owner, Track? track) => _holders.hold(owner, track);

  @override
  void release(Object owner) => _holders.release(owner);
}

/// Plays through audioplayers: a pool per sound, one looping player for the
/// music and one for the place's sounds; quiet while the app is in the
/// background.
class SystemSounds implements Sounds {
  SystemSounds() {
    _lifecycle = AppLifecycleListener(onHide: () => _setAway(true), onShow: () => _setAway(false));
  }

  static const _sfxVolume = 0.85, _musicVolume = 0.35, _ambienceVolume = 0.3;

  late final AppLifecycleListener _lifecycle;
  final _pools = <String, Future<AudioPool>>{};
  final _holders = TrackHolders();
  Future<void>? _setUp;
  AudioPlayer? _loop, _amb;
  Music? _playing;
  String? _ambPlaying;
  var _music = true, _effects = true, _away = false;

  @override
  set music(bool on) {
    _music = on;
    _update();
  }

  @override
  set effects(bool on) => _effects = on;

  void _setAway(bool away) {
    _away = away;
    _update();
  }

  Future<void> _ready() => _setUp ??= AudioPlayer.global.setAudioContext(
        AudioContextConfig(focus: AudioContextConfigFocus.mixWithOthers, respectSilence: true).build(),
      );

  @override
  void play(String sfx) {
    if (!_effects || _away || sfx.isEmpty) return;
    unawaited(_play(sfx));
  }

  Future<void> _play(String sfx) async {
    try {
      await _ready();
      final pool = await (_pools[sfx] ??= AudioPool.createFromAsset(path: 'sounds/$sfx.wav', maxPlayers: 3));
      await pool.start(volume: _sfxVolume);
    } catch (_) {
      _pools.remove(sfx);
    }
  }

  @override
  void hold(Object owner, Track? track) {
    _holders.hold(owner, track);
    _update();
  }

  @override
  void release(Object owner) {
    _holders.release(owner);
    _update();
  }

  void _update() {
    final track = _away ? null : _holders.current;
    final music = _music ? track?.music : null;
    // The place's sounds go with the effects switch (they are not music).
    final amb = _effects ? track?.ambience : null;
    if (music != _playing) {
      _playing = music;
      unawaited(_switchMusic(music));
    }
    if (amb != _ambPlaying) {
      _ambPlaying = amb;
      unawaited(_switchAmbience(amb));
    }
  }

  Future<AudioPlayer> _looping(AudioPlayer? p, void Function(AudioPlayer) keep) async {
    if (p != null) return p;
    final made = AudioPlayer();
    keep(made);
    await made.setReleaseMode(ReleaseMode.loop);
    return made;
  }

  Future<void> _switchMusic(Music? music) async {
    try {
      await _ready();
      final loop = await _looping(_loop, (p) => _loop = p);
      await loop.stop();
      if (music == null || music != _playing) return;
      await loop.setVolume(_musicVolume);
      await loop.play(AssetSource('sounds/${music.file}.wav'));
    } catch (_) {}
  }

  Future<void> _switchAmbience(String? file) async {
    try {
      await _ready();
      final loop = await _looping(_amb, (p) => _amb = p);
      await loop.stop();
      if (file == null || file != _ambPlaying) return;
      await loop.setVolume(_ambienceVolume);
      await loop.play(AssetSource('sounds/$file.wav'));
    } catch (_) {}
  }

  void dispose() {
    _lifecycle.dispose();
    unawaited(_loop?.dispose());
    unawaited(_amb?.dispose());
  }
}
