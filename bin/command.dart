import 'person.dart';

// Імпорт усіх команд
import 'com/moder.dart';
import 'com/admin.dart';
import 'com/whoiam.dart';
import 'com/credit.dart';
import 'com/help.dart';
import 'com/leaderboard.dart';

class CommandResult {
  String text;
  int deleteUserMessageAfterSeconds;
  int deleteBotMessageAfterSeconds;
  bool hasImage;

  CommandResult({
    required this.text,
    this.deleteUserMessageAfterSeconds = 0,
    this.deleteBotMessageAfterSeconds = 0,
    this.hasImage = false,
  });
}

/// Абстрактна команда
abstract class Command {
  /// Ім’я команди (наприклад: "допомога" чи "команди")
  String get name;

  /// Наприклад, повідомлення "/help", але slashName пропускає перший слеш
  String get slashName;

  /// Опис команди
  String get description;

  /// Мінімальна роль, яка має доступ
  Role get minRole => Role.user;

  /// Скільки секунд тримати повідомлення користувача (0 = не видаляти)
  int get deleteUserMessageAfterSeconds => 0;

  /// Скільки секунд тримати повідомлення бота (0 = не видаляти)
  int get deleteBotMessageAfterSeconds => 0;

  /// Виконання команди
  Future<String> execute(Person actor, Person? target, Iterable<String> args);

  static List<Command> all = [ // Список усіх команд
    // help.dart
    HelpCommand(),  // "допомога" - Основна команда для допомоги
    Help2Command(), // "команди" - Альтернативна команда для допомоги
    DebugPrintCommand(), // "debug" - команда для дебаґу

    // admin.dart
    AdminCommand(),    // "адмін" - Основна команда для адмінів
    AddAdminCommand(), // "+адмін" - Додати роль адміна
    SubAdminCommand(), // "-адмін" - Зняти роль адміна

    // whoiam.dart
    WhoAmICommand(),  // "я" - Інформація про себе
    
    // moder.dart
    ModerCommand(),    // "інспектор" - Основна команда для інспекторів
    AddModerCommand(), // "+інспектор" - Додати роль інспектора
    SubModerCommand(), // "-інспектор" - Зняти роль інспектора

    // credit.dart
    AddSocialCredit(), // "+" - Додати соц. кредити
    SubSocialCredit(), // "-" - Відняти соц. кредити

    // leaderboard.dart
    BestLeaderboardCommand(),
    WorstLeaderboardCommand(),
    // інші...
  ];
}

