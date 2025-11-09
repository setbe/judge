import '../person.dart';
import '../command.dart';

import "whoiam.dart";

class AddSocialCredit extends Command {
  @override
  String get name => "+";

  @override
  String get slashName => "give";

  @override
  String get description => "Дає соц. кредити, якщо ВІДПОВІСТИ на повідомлення";

  @override
  Role get minRole => Role.moder;

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    if (target == null) return "❌ Помилка: не вказано користувача.";
    if (args.isEmpty) return "❌ Помилка: не вказано кількість кредитів.";
    int positiveAmount = Person.parseSocialCredits(args.first); // Парсимо кількість кредитів
    if (positiveAmount <= 0) return "❌ Помилка: \"${args.first}\" некоректна кількість кредитів. Може команда /take ?";
    final oldCredits = target.socialCredits; // Записуємо початковий баланс цілі

    if (actor.role == Role.moder) { // Якщо інспектор, перевіряємо ліміт
      int left = actor.dailySocialCreditsLeft - positiveAmount;
      if (positiveAmount > actor.dailySocialCreditsLeft) {
        positiveAmount = actor.dailySocialCreditsLeft; // Обмежуємо до залишку ліміту
        left = positiveAmount; // Вичерпуємо ліміт
      }
      actor.setDailyCreditsLeft(left); // Встановлюємо поточний залишок видачі
      await actor.save(); // Оновлюємо інспектора
    }
    // Проводимо операцію оновлення цільового користувача
    target.addSocialCredits(positiveAmount);
    await target.save();

    // Набір частин тексту для виводу
    final strOldCredits = Person.socialCreditsStrFromInt(oldCredits);
    final strPositiveAmount = Person.socialCreditsStrFromInt(positiveAmount);
    final strSocialCredits = Person.socialCreditsStrFromInt(target.socialCredits);
    return await WhoAmICommand.executeFor(target, "$strOldCredits + $strPositiveAmount = $strSocialCredits");
  }
}

class SubSocialCredit extends Command {
  @override
  String get name => "-";

  @override
  String get slashName => "take";

  @override
  String get description => "Віднімає соц. кредити, якщо ВІДПОВІСТИ на повідомлення";

  @override
  Role get minRole => Role.moder;

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    if (target == null) return "❌ Помилка: не вказано користувача.";
    if (args.isEmpty) return "❌ Помилка: не вказано кількість кредитів.";
    int positiveAmount = Person.parseSocialCredits(args.first); // Парсимо кількість кредитів
    if (positiveAmount <= 0) return "❌ Помилка: \"${args.first}\" некоректна кількість кредитів. Може, команда /give ?";
    
    final oldCredits = target.socialCredits; // Записуємо початковий баланс цілі
    // Якщо інспектор, перевіряємо ліміт
    if (actor.role == Role.moder) {
      int left = actor.dailySocialCreditsLeft - positiveAmount;
      if (positiveAmount > actor.dailySocialCreditsLeft) {
        positiveAmount = actor.dailySocialCreditsLeft; // Обмежуємо до залишку ліміту
        left = positiveAmount; // Вичерпуємо ліміт
      }
      actor.setDailyCreditsLeft(left); // Встановлюємо поточний залишок видачі
      await actor.save();
    }
    // Проводимо операцію оновлення цільового користувача
    final amount = -positiveAmount; // Переводимо в негативне число, оскільки це команда віднімання
    target.addSocialCredits(amount);
    await target.save();

    // Додавання замітки користувачу
    await processFuckUp(target, args);

    // Набір частин тексту для виводу
    final strOldCredits = Person.socialCreditsStrFromInt(oldCredits);
    final strPositiveAmount = Person.socialCreditsStrFromInt(positiveAmount);
    final strSocialCredits = Person.socialCreditsStrFromInt(target.socialCredits);
    return await WhoAmICommand.executeFor(target, "$strOldCredits - $strPositiveAmount = $strSocialCredits");
  } // execute

  Future<void> processFuckUp(Person target, Iterable<String> args) async {
    // 2-ий елемент (і наступні) це причина fuck up'пу
    final fuckUpMessage = args.length > 1
        ? args.skip(1).join(' ')
        : null;
    if (fuckUpMessage == null) return;

    target.setFuckUpToday(await target.getFuckUpBySocialCredits(target.socialCredits));
    target.lastSocialCreditNotice = fuckUpMessage;
    await target.save();
  } // processFuckUp
}