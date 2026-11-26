/// The app's version, as in pubspec.yaml (CI passes it in with
/// --dart-define=APP_VERSION; test/version_test.dart checks they agree).
const appVersion = String.fromEnvironment('APP_VERSION', defaultValue: '0.1.1');
