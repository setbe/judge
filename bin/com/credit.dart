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
    // Перевіряємо, чи має користувач достатньо прав
    if (actor.role.index < Role.moder.index) {
      return "❌ Помилка: недостатньо прав для виконання цієї команди.";
    }

    // Перевіряємо, чи є цільовий користувач
    if (target == null) return "❌ Помилка: не вказано користувача.";

    // Перевіряємо, чи вказано кількість кредитів (другим елементом)
    if (args.isEmpty) return "❌ Помилка: не вказано кількість кредитів.";

    // Парсимо кількість кредитів
    int positiveAmount = Person.parseSocialCredits(args.first);
    if (positiveAmount <= 0) return "❌ Помилка: \"${args.first}\" некоректна кількість кредитів.";
  
    // Записуємо початковий баланс цілі
    final oldCredits = target.socialCredits;
    
    // Якщо інспектор, перевіряємо ліміт
    if (actor.role == Role.moder) {
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
    // Перевіряємо, чи є цільовий користувач
    if (target == null) return "❌ Помилка: не вказано користувача.";

    // Перевіряємо, чи вказано кількість кредитів (другим елементом)
    if (args.isEmpty) return "❌ Помилка: не вказано кількість кредитів.";

    // Парсимо кількість кредитів
    int positiveAmount = Person.parseSocialCredits(args.first);
    // Увага: парсимо лише позитивне число, бо '+' або '-' це перший аргумент, а не частина числа
    if (positiveAmount <= 0) return "❌ Помилка: \"${args.first}\" некоректна кількість кредитів.";
  
    // Записуємо початковий баланс цілі
    final oldCredits = target.socialCredits;
    
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