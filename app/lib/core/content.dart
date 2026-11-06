/// The fixed things the game is made of: the six places, the four games,
/// the three ages and the three drawing styles (docs/design.md).
library;

/// The places (docs/design.md 「場景」); each has assets/scenes/<name>.json
/// and its drawings in assets/art/<style>/<name>/.
enum Place {
  park('公園', 'park'),
  market('夜市', 'night market'),
  beach('海邊', 'beach'),
  zoo('動物園', 'zoo'),
  party('生日派對', 'birthday party'),
  kitchen('廚房', 'kitchen');

  const Place(this.zh, this.en);

  final String zh;
  final String en;

  /// Free to play before the full version is bought (docs/design.md 「以後上架」).
  bool get free => this == park || this == beach;
}

/// How old the child is, which sets how hard the puzzles are.
enum Level {
  small('小小', '2～3 歲'),
  mid('中', '3～4 歲'),
  big('大', '4～5 歲');

  const Level(this.zh, this.ages);

  final String zh;
  final String ages;

  T pick<T>(T small, T mid, T big) => switch (this) {
        Level.small => small,
        Level.mid => mid,
        Level.big => big,
      };
}

/// The four games (docs/design.md 「四種玩法」) and the age each starts at.
enum Mode {
  odd('哪一個不一樣？', Level.small),
  change('小變變了什麼？', Level.small),
  two('兩張找不同', Level.mid),
  hide('小變躲在哪裡？', Level.small);

  const Mode(this.zh, this.from);

  final String zh;
  final Level from;
}

/// The three drawing styles; every one draws the same scene, so switching
/// never changes a puzzle.
enum Style {
  /// 等角小模型風 (the default).
  a('小模型'),

  /// 孔版印刷風.
  b('版畫'),

  /// 粗蠟筆童畫風.
  c('蠟筆');

  const Style(this.zh);

  final String zh;

  Style get next => Style.values[(index + 1) % Style.values.length];
}
