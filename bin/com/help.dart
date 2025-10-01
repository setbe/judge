import '../person.dart';
import '../command.dart';

class HelpCommand extends Command {
  @override
  String get name => "допомога";

  @override
  String get slashName => "help";

  @override
  String get description => "Допомога по командам";

  @override
  int get deleteUserMessageAfterSeconds => 30;

  @override
  int get deleteBotMessageAfterSeconds => 0; // повідомлення видаляється через 30 секунд

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    Person person;
    // Якщо є цільова особа і її роль не вища за роль актора, показуємо їй довідку
    if (target != null && actor.role.index >= target.role.index) {
      person = target;
    } else {
      person = actor;
    }
    return await executeFor(person);
  }

  Future<String> executeFor(Person person) async {
    return """
Source code: github.com/setbe/judge
${person.role == Role.moder ? "Ліміт сьогодні: ${person.dailyCreditsStr} кредитів" : ""}
Команди:
🎰
/i - суд я - інформація про тебе
/help - суд допомога - ця довідка
/highscore - суд кращі - таблиця з кращими
/lowscore - суд гірші - таблиця з гіршими
${person.role.index > Role.user.index ? "/inspector - суд інспекція - інспекторська мєтодичка" : ""}
${person.role == Role.admin ? "/admin - суд адмін - адмінська довідка" : ""}
""";
  }
}

class Help2Command extends Command {
  @override
  String get name => "команди";

  @override
  String get slashName => "commands";

  @override
  String get description => "Допомога по командам";

  @override
  int get deleteUserMessageAfterSeconds => 30;

  @override
  int get deleteBotMessageAfterSeconds => 0; // повідомлення видаляється через 30 секунд

  @override
  Future<String> execute(Person person, Person? target, Iterable<String> args) async {
    return HelpCommand().execute(person, target, args); // Виклик схожою за назвою командою
  }
}

class DebugPrintCommand extends Command {
  @override
  String get name => "debug";

  @override
  String get slashName => "judge_debug";

  @override
  String get description => "Вивід інформації про користувача";

  @override
  Role get minRole => Role.admin;

  @override
  int get deleteUserMessageAfterSeconds => 1;

  @override
  int get deleteBotMessageAfterSeconds => 20; // повідомлення видаляється через 20 секунд

  @override
  Future<String> execute(Person person, Person? target, Iterable<String> args) async {
    return await Person.debugString(target ?? person);
  }
}