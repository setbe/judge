import 'package:dotenv/dotenv.dart';
import 'person.dart'; // Для Platform

/// Sigleton сервіс для роботи з оточенням (env)
class EnvService {
  EnvService._privateConstructor();
  static final EnvService _instance = EnvService._privateConstructor();
  static EnvService get instance => _instance;

  bool _initialized = false;
  String? _telegramOwnerUsername;
  String? _discordOwnerUsername;
  String? _botTelegramToken;
  String? _botDiscordToken;

  Iterable<int> _whitelistTelegram = const [];
  Iterable<int> _whitelistDiscord = const [];

  Future<void> init({Iterable<String> envPaths = const ['.env']}) async {
    if (_initialized) return;
    // В чистому Dart використовуємо dotenv: dotenv..load();
    final env = DotEnv()..load(envPaths); // Створення об'єкта DotEnv
    _telegramOwnerUsername = env['TELEGRAM_OWNER_USERNAME']; // Нік власника Telegram
    _discordOwnerUsername = env['DISCORD_OWNER_USERNAME']; // Нік власника Discord
    _botTelegramToken = env['BOT_TELEGRAM_TOKEN']; // Шукаємо BOT_TOKEN для Telegram бота
    _botDiscordToken = env['BOT_DISCORD_TOKEN']; // Шукаємо BOT_TOKEN для Discord бота
   
    // Парсимо whitelist-и
    _whitelistTelegram = _parseWhitelist(env['WHITELIST_TELEGRAM']);
    _whitelistDiscord = _parseWhitelist(env['WHITELIST_DISCORD']);

    _initialized = true;
    if (_telegramOwnerUsername == null) throw Exception("❌ Помилка: немає TELEGRAM_OWNER_USERNAME у .env");
    if (_discordOwnerUsername == null) throw Exception("❌ Помилка: немає DISCORD_OWNER_USERNAME у .env");
    if (_botTelegramToken == null) throw Exception("❌ Помилка: немає BOT_TELEGRAM_TOKEN у .env");
    if (_botDiscordToken == null) throw Exception("❌ Помилка: немає BOT_DISCORD_TOKEN у .env");
  }

  bool inWhitelist(int roomId, Platform platform) {
    if (!_initialized) throw Exception('EnvService не ініціалізований');
    switch (platform) {
      case Platform.telegram:
        return _whitelistTelegram.contains(roomId);
      case Platform.discord:
        return _whitelistDiscord.contains(roomId);
    }
  }

  String ownerUsername(Platform platform) {
    if (!_initialized) throw Exception('EnvService не ініціалізований');
    return _telegramOwnerUsername ?? '';
  }

  String getBotToken(Platform platform) {
    if (!_initialized) throw Exception('EnvService не ініціалізований');
    switch (platform) {
      case Platform.telegram: return _botTelegramToken ?? '';
      case Platform.discord: return _botDiscordToken ?? '';
    }
    
  }

  Iterable<int> _parseWhitelist(String? raw) {
    if (raw == null || raw.trim().isEmpty) return const [];
    return raw
        .split(';')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .map(int.parse)
        .toList();
  }

}