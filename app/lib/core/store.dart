import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Where the game is kept: one small JSON file on the phone (no account,
/// nothing goes online).
abstract interface class GameStore {
  Future<Map<String, dynamic>?> read();

  /// Saves [json]; saves are done in order, the last one wins.
  void write(Map<String, dynamic> json);

  /// Done with the saves asked for so far.
  Future<void> flush();
}

class FileStore implements GameStore {
  FileStore(Directory dir) : _file = File('${dir.path}/sharp_eyes.json');

  final File _file;
  Future<void> _queue = Future.value();

  @override
  Future<Map<String, dynamic>?> read() async {
    for (final f in [_file, File('${_file.path}.bak')]) {
      try {
        if (await f.exists()) return jsonDecode(await f.readAsString()) as Map<String, dynamic>;
      } catch (_) {
        // A broken file: try the copy from the save before.
      }
    }
    return null;
  }

  @override
  void write(Map<String, dynamic> json) {
    final text = jsonEncode(json);
    _queue = _queue.then((_) async {
      try {
        // Written beside it and then swapped in, so a phone switched off
        // halfway leaves the old file whole.
        final tmp = File('${_file.path}.tmp');
        await tmp.writeAsString(text, flush: true);
        if (await _file.exists()) await _file.copy('${_file.path}.bak');
        await tmp.rename(_file.path);
      } catch (_) {}
    });
  }

  @override
  Future<void> flush() => _queue;
}

/// Keeps the game in memory (tests).
class MemoryStore implements GameStore {
  MemoryStore([this.saved]);

  Map<String, dynamic>? saved;

  @override
  Future<Map<String, dynamic>?> read() async => saved;

  @override
  void write(Map<String, dynamic> json) => saved = jsonDecode(jsonEncode(json)) as Map<String, dynamic>;

  @override
  Future<void> flush() async {}
}
