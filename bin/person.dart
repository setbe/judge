// Коротко для чистого Dart:
// 
// 1. Отримати пакети:
// ```
// dart pub get
// ```
// 2. Перегенерувати:
// ```
// dart run build_runner build --delete-conflicting-outputs
// ```
// 3. Якщо проблеми — очистити і згенерувати знову:
// ```
// dart run build_runner clean
// dart run build_runner build --delete-conflicting-outputs
// ```


import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:hive/hive.dart';

import 'config.dart';

part 'person.g.dart';


/// Роль користувача
@HiveType(typeId: 0)
enum Role {
  @HiveField(0)
  user,
  @HiveField(1)
  moder,
  @HiveField(2)
  admin,
}

/// Поки що ніде не використовується, реалізовано на майбутнє
@HiveType(typeId: 2)
enum UserState {
  @HiveField(0)
  neutral,
  @HiveField(1)
  good,
  @HiveField(2)
  bad,
}

/// Зручний енум для вибору платформи
@HiveType(typeId: 3)
enum Platform {
  @HiveField(0)
  telegram,
  @HiveField(1)
  discord,
}

/// Енум для позначки того, наскільки користувач показав себе погано
@HiveType(typeId: 4)
enum FuckUp {
  @HiveField(0)
  none,
  @HiveField(1)
  light,
  @HiveField(2)
  medium,
  @HiveField(3)
  high,
  @HiveField(4)
  fatal
}


/// Головний клас користувача. Кросплатформений.
/// Цей клас зберігає "характеристики" всіх осіб і взаємодіє з лібою Hive.
@HiveType(typeId: 1)
class Person extends HiveObject {

  /// ========= Telegram =========
  /// телеграм айді
  @HiveField(0)
  int? telegramId;
  /// відубражуване ім'я
  @HiveField(1)
  String? telegramName;
  /// нікнейм
  @HiveField(2) 
  String? telegramUsername;

  /// ========= Роль =========
  // користувач, модератор, адміністратор
  @HiveField(3)
  Role role;

  /// ========= Динамічна мапа даних =========
  // Якісь інші дані
  @HiveField(4)
  Map<String, dynamic> other;

  /// ========= Discord =========
  /// діскорд айді
  @HiveField(5)
  int? discordId;
  /// відубражуване ім'я 
  @HiveField(6)
  String? discordName;
  /// нікнейм
  @HiveField(7)
  String? discordUsername;

  /// ========= Соц кредити =========
  /// соціальні кредити
  @HiveField(8)
  int _socialCredits;

  /// ========= Стан =========
  /// нейтральний, хороший, поганий
  @HiveField(9)
  UserState state;

  /// ========= Соціальна Замітка =========
  /// причина "покарання/похвали"
  @HiveField(10)
  String? _lastSocialCreditNotice;
  /// дата причини "покарання/похвали"
  @HiveField(11)
  DateTime? _lastSocialCreditNoticeDate;

  /// ========= Інспекторам ліміт =========
  /// Щоденний ліміт соц. кредитів на додавання
  @HiveField(12)
  int _dailySocialCreditsLeft;
  /// Всього щоденних соц. кредитів (для відновлення)
  @HiveField(13)
  int _dailySocialCreditsLimit;

  /// ========= Датовані прапорці =========
  /// Остання дата використання казино
  @HiveField(14)
  DateTime? lastUsedCasinoDate;
  /// Остання дата використання персони
  @HiveField(15)
  DateTime? lastUsedPersonaDate;

  /// ========= Булеві прапорці =========
  /// Остання дата використання персони
  @HiveField(16)
  bool hasGeneratedImageBySystem;

  
  /// Тижневий запис розчарувань через користувача
  @HiveField(17)
  List<FuckUp> _fuckUpsPerWeek = List<FuckUp>.filled(7, FuckUp.none, growable: false);

  // Текст заданий як статус користувача цим же користувачем при команді "суд я"
  @HiveField(18)
  String? userStatusText;
  
  /// Комбо і лічильник щоденних казино підряд
  @HiveField(19)
  int casinoStreak = 0;
  

  // --- Конструктор ---
  Person({
    int? id,
    String? name,
    String? username,
    Platform? platform,
    this.role = Role.user,
    Map<String, dynamic>? other,
    int socialCredits = 0,
    this.state = UserState.neutral,
    int dailySocialCreditsLeft = 5000,
    int dailySocialCreditsLimit = 5000,
    this.hasGeneratedImageBySystem = false,
    List<FuckUp>? fuckUpsPerWeek,
    
  })  : other = other ?? { 'createdAt': DateTime.now().toIso8601String(), },
        _socialCredits = socialCredits,
        _dailySocialCreditsLeft = dailySocialCreditsLeft,
        _dailySocialCreditsLimit = dailySocialCreditsLimit {
    tzdata.initializeTimeZones();
    if (platform == Platform.telegram) {
      telegramId = id;
      telegramName = name;
      telegramUsername = username;
    } else if (platform == Platform.discord) {
      discordId = id;
      discordName = name;
      discordUsername = username;
    }
    _fuckUpsPerWeek = fuckUpsPerWeek ?? List<FuckUp>.filled(7, FuckUp.none, growable: false);
  }

  static Future<String> debugString(Person p) async {
  final buffer = StringBuffer();

  // Цей перший рядок НЕ ЗМІНЮВАТИ. Він потрібен для однієї милиці.
  buffer.writeln("===== Person Debug =====");

  // Заповнюємо даними користувача
  buffer.writeln("Telegram: id=${p.telegramId}, name=${p.telegramName}, username=${p.telegramUsername}");
  buffer.writeln("Discord : id=${p.discordId}, name=${p.discordName}, username=${p.discordUsername}");
  buffer.writeln("Role    : ${p.role}");
  buffer.writeln("State   : ${p.state}");
  buffer.writeln("Credits : ${p._socialCredits}");
  buffer.writeln("Daily   : ${p._dailySocialCreditsLeft}/${p._dailySocialCreditsLimit}");
  buffer.writeln("Casino  : lastUsed=${p.lastUsedCasinoDate}, streak=${p.casinoStreak}");
  buffer.writeln("Persona : lastUsed=${p.lastUsedPersonaDate}");
  buffer.writeln("Status  : ${p.userStatusText ?? "-"}");
  buffer.writeln("Other   : ${p.other}");

  return buffer.toString();
}

  // =====================
  // Константи для нескінченності
  // =====================
  static const int _maxInt = 9223372036854775807; // 64-bit max
  static const int _minInt = -9223372036854775808; // 64-bit min

  static const int positiveInfinity = _maxInt;
  static const int negativeInfinity = _minInt;


  // =====================
  // Платформозалежні ґеттери
  // =====================
  String name(Platform? platform) {
    switch (platform ?? this.platform) {
      case Platform.telegram: return telegramName ?? "*Невідомий*";
      case Platform.discord: return discordName ?? "*Невідомий*";
    }
  }

  void setUsername(Platform? platform, String newUsername) {
    switch (platform ?? this.platform) {
      case Platform.telegram: telegramUsername = newUsername; break;
      case Platform.discord: discordUsername = newUsername; break;
    }
  }

  String username(Platform? platform) {
    switch (platform ?? this.platform) {
      case Platform.telegram: return telegramUsername ?? "*невідомий_нік*";
      case Platform.discord: return discordUsername ?? "*невідомий_нік*";
    }
  }

  int id(Platform? platform) {
    switch (platform ?? this.platform) {
      case Platform.telegram: return telegramId ?? 0;
      case Platform.discord: return discordId ?? 0;
    }
  }
  Platform get platform => telegramId != null ? Platform.telegram : Platform.discord;

  /// Геттер для всього масиву (не змінює порядок)
  List<FuckUp> get fuckUpsPerWeek => List.unmodifiable(_fuckUpsPerWeek);

  /// Сеттер для поточного дня тижня за Києвом
  void setFuckUpToday(FuckUp value) {
    final kyivTime = tz.TZDateTime.now(tz.getLocation('Europe/Kyiv'));
    final index = kyivTime.weekday % 7; // weekday: 1=Пн ... 7=Нд -> 0=Нд ... 6=Сб
    // print(kyivTime); працює правильно
    _fuckUpsPerWeek[index] = value;
  }

  /// Повертає середній рівень FuckUp за тиждень
  /// Вибирає найчастіше значення, якщо рівні частоти, повертає максимальний
  FuckUp averageFuckUp() {
    final counts = <FuckUp, int>{};
    for (var f in _fuckUpsPerWeek) {
      counts[f] = (counts[f] ?? 0) + 1;
    }

    // Сортуємо спочатку за кількістю, потім за порядком enum (index)
    var sorted = counts.entries.toList()
      ..sort((a, b) {
        if (b.value != a.value) return b.value.compareTo(a.value);
        return b.key.index.compareTo(a.key.index);
      });

    return sorted.first.key;
  }

  // =====================
  // Інкапсуляція Social Credits
  // =====================

  /// Повертає кредити у вигляді рядка
  String get socialCreditsStr {
    if (_socialCredits == _maxInt) return "∞";
    if (_socialCredits <= _minInt + 1) return "-∞";
    return _socialCredits.toString();
  }

  static String socialCreditsStrFromInt(int amount) {
    if (amount == _maxInt) return "∞";
    if (amount <= _minInt + 1) return "-∞";
    return amount.toString();
  }

  /// Додає/віднімає кредити з урахуванням меж
  void addSocialCredits(int value) {
    final res = _socialCredits + value;
    _socialCredits = (res >= _maxInt ||
                      value == _maxInt) ? _maxInt
                     : (res <= _minInt || 
                        value == _minInt) ? _minInt
                     : res;
  }

  /// Конвертація рядка в int (парсер концепту +00/-00)
  /// Повертає 0, якщо не вийшло розпарсити
  static int parseSocialCredits(String s) {
    if (s == "00") return _maxInt;
    if (s == "-00") return _minInt;
    return int.tryParse(s) ?? 0;
  }

  int get socialCredits => _socialCredits;

  // =====================
  // Інкапсуляція Daily Social Credits
  // =====================

  String get dailyCreditsStr {
    if (_dailySocialCreditsLeft >= _maxInt) return "∞";
    if (_dailySocialCreditsLeft <= _minInt + 1) return "-∞";
    return _dailySocialCreditsLeft.toString();
  }

  void addDailyCredits(int value) => 
    _dailySocialCreditsLeft = shrinkSocialCredits(_dailySocialCreditsLeft + value);

  /// Встановлення ліміту соц. кредитів (для інспекторів)
  void setDailySocialCreditsLimit(int value) => _dailySocialCreditsLimit = shrinkSocialCredits(value);
  void setDailyCreditsLeft(int value) => _dailySocialCreditsLeft = shrinkSocialCredits(value);
  int shrinkSocialCredits(int value) => 
        (value >= _maxInt) ? _maxInt 
        : (value <= _minInt) ? _minInt 
        : value;

  int get dailySocialCreditsLeft => _dailySocialCreditsLeft;
  int get dailySocialCreditsLimit => _dailySocialCreditsLimit;
 
  Future<FuckUp> getFuckUpBySocialCredits(int s) async {
    final k1   = JudgeConfig.instance.fuckUpSocialCreditsPenaltyK1;
    final k10  = JudgeConfig.instance.fuckUpSocialCreditsPenaltyK10;
    final k100 = JudgeConfig.instance.fuckUpSocialCreditsPenaltyK100;

    // Лише позитивне число
    s = s.abs();
    
    if (s <= k1) return FuckUp.light;
    if (s <= k10) return FuckUp.medium;
    if (s <= k100) return FuckUp.high;
    return FuckUp.fatal;
  }

  String? get lastSocialCreditNotice {
    final dateNotice = _lastSocialCreditNoticeDate;
    if (dateNotice == null) return null;

    final dateNow = DateTime.now();
    final diff = dateNow.difference(dateNotice);

    // Просто рахуємо різницю, якщо різниця
    // більше 2 днів, ми "забуваємо" про замітку
    if (diff.inDays > JudgeConfig.instance.daysToForgetUserNotice) {
      return null;
    }
    return _lastSocialCreditNotice;
  }

  set lastSocialCreditNotice(String? msg) {
    _lastSocialCreditNotice = msg;
    _lastSocialCreditNoticeDate = DateTime.now();
  }

    /// Шлях до останнього згенерованого зображення (якщо існує)
    /// Якщо існує повертає шлях і скидує прапорець що зображення нема,
    /// але зображення застоюється на диску і постійно перезаписується новими зображеннями.
  String? get pollLastGeneratedImage {
    final basePath = Person.getUserGeneratedImagePath(platform);
    if (!hasGeneratedImageBySystem) return null;
    hasGeneratedImageBySystem = false;
    save();
    final filename = "${id(platform)}.jpg";
    return "$basePath/$filename";
  }

  /// Статичний метод для вибору базового шляху по платформі
  static String getUserGeneratedImagePath(Platform platform) {
    switch (platform) {
      case Platform.telegram:
        return "data/img/users/telegram";
      case Platform.discord:
        return "data/img/users/discord";
    }
  }

}
