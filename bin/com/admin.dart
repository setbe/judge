import '../person.dart';
import '../command.dart';
import '../user_repository.dart';

class AdminCommand extends Command {
  @override
  String get name => "адмін";

  @override
  String get slashName => "admin";

  @override
  String get description => "Адмінська довідка";

  @override
  Role get minRole => Role.admin;

  @override
  Future<String> execute(Person person, Person? target, Iterable<String> args) async {
    return """
== Нагородити/конфіскувати ==:
/give <кількість> 
/take <кількість> 
суд + <кількість>
суд - <кількість>

== Найняти або зняти з посади ==
/admin+ <@username>
/admin- <@username>
/inspector+ <@username>
/inspector- <@username>
суд +адміністратор <@username>
суд -адміністратор <@username>
суд +інспектор <@username> <щоденний ліміт>
суд -інспектор <@username> <щоденний ліміт>

'@username' НЕ потрібен, якщо ВІДПОВІДАТИ на повідомлення
""";
  }
}

class AddAdminCommand extends Command {
  @override
  String get name => "+адміністратор";

  @override
  String get slashName => "admin+";

  @override
  String get description => "Додати користувачу роль адміна";

  @override
  Role get minRole => Role.admin;

  @override
  Future<String> execute(Person person, Person? target, Iterable<String> args) async {
    if (target == null) return '❌ Помилка: не вказано користувача.';
    if (target.role == Role.admin) return '❌ Помилка: користувач вже є адміном.';
    target.role = Role.admin;
    await UserRepository.instance.updateUser(target);
    return '✅ ${target.name(null)} підвищено до посади адміністратора.';
  }
}

class SubAdminCommand extends Command {
  @override
  String get name => "-адміністратор";

  @override
  String get slashName => "admin-";

  @override
  String get description => "Зняти з користувача роль адміна";

  @override
  Role get minRole => Role.admin;

  @override
  Future<String> execute(Person person, Person? target, Iterable<String> args) async {
    if (target == null) return '❌ Помилка: не вказано користувача.';
    if (target.role != Role.admin) return '❌ Помилка: користувач НЕ є адміном.';
    target.role = Role.user;
    await UserRepository.instance.updateUser(target);
    return '✅ ${target.name(null)} знято з посади адміністратора.';
  }
}