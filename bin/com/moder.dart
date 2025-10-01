import '../person.dart';
import '../command.dart';
import '../user_repository.dart';

class ModerCommand extends Command {
  @override
  String get name => "інспекція";

  @override
  String get slashName => "inspector";

  @override
  String get description => "Інспекторська мєтодичка";

  @override
  Role get minRole => Role.moder;

  @override
  Future<String> execute(Person person, Person? target, Iterable<String> args) async {
    return """
Щоденний ліміт ${person.dailyCreditsStr} кредитів для:
== Нагородити/конфіскувати ==:
/give <кількість> 
/take <кількість> 
суд + <кількість>
суд - <кількість>
""";
  }
}

class AddModerCommand extends Command {
  @override
  String get name => "+інспектор";

  @override
  String get slashName => "hire_inspector";

  @override
  String get description => "Додати користувачу роль інспектора";

  @override
  Role get minRole => Role.admin;

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    if (target == null) return '❌ Помилка: не вказано користувача.';
    final bool wasUserBefore = target.role == Role.user;
    final bool wasAdminBefore = target.role == Role.admin;

    // Перевіряємо, чи вказано кількість кредитів (другим елементом)
    if (args.isEmpty) return "❌ Помилка: не вказано кількість кредитів.";

    // Парсимо кількість кредитів
    final limit = Person.parseSocialCredits(args.first);
    if (limit <= 0) return "❌ Помилка: некоректна кількість кредитів.";

    // Записуємо початковий ліміт інспектора
    final oldLimit = target.dailySocialCreditsLimit;

    // Оновлення інспектора
    target.role = Role.moder;
    target.setDailySocialCreditsLimit(limit);
    await UserRepository.instance.updateUser(target);
    
    final stonksMsg = (wasUserBefore) ? "громадянин -> інспектор ⬆📈" : 
                      (wasAdminBefore) ? "адміністратор -> інспектор ⬇" : "";
    final limitMsg = (oldLimit > limit) ? "ліміт $oldLimit 💸 -> $limit ⬇💵" : "ліміт $oldLimit 💵 -> ⬆💸 $limit";
    return """
✅ ${target.name(null)}
$stonksMsg
$limitMsg
""";
  }
}

class SubModerCommand extends Command {
  @override
  String get name => "-інспектор";

  @override
  String get slashName => "fire_inspector";

  @override
  String get description => "Зняти з користувача роль інспектора";

  @override
  Role get minRole => Role.admin;

  @override
  Future<String> execute(Person person, Person? target, Iterable<String> args) async {
    return 'Команда виконана!';
  }
}
