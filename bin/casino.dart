// Локальні імпорти
import 'dart:math';

import 'command.dart';
import 'com/credit.dart' as credit;
import 'telegram.dart' as tg;
import 'person.dart';
import 'config.dart';
import 'utils.dart' as utils;

import 'com/image/image.dart';
import 'com/image/casino_image.dart';
// Пакети для роботи з Telegram API та середовищем
import 'package:teledart/model.dart';

// Всі можливі емоджі в казино:
// "🅱️", "🍇", "🍋", "7️⃣"
const casinoEmoji = {"🅱️", "🍇", "🍋", "7️⃣"};

class CasinoResult {
  // Змінні з якими багато працюватимемо: встановлюємо початкові значення.
  bool jackpot = false;
  int reward = 0;
  DrawRequest drawRequest = DrawRequest.none;

  // Мені дуже подобається, що я придумав змінну "isNegative" та
  // ЗАВЖДИ тримаю значення нагороди ПОЗИТИВНИМ числом.
  bool isNegative = false;

  CasinoResult((String, String, String) r) {
    // Означає мінусову нагороду
    isNegative = _deduceIsNegativeReward(r);

    // 🅱️🅱️🅱️ або 🍇🍇🍇 або 🍋🍋🍋 або 7️⃣7️⃣7️⃣
    if (r.$1 == r.$2 && r.$2 == r.$3) {
      drawRequest = isNegative 
        ? DrawRequest.casinoNegative3 
        : DrawRequest.casino3;
      reward = JudgeConfig.instance.casinoRewardHigh;
      jackpot = _randomizeJackpot();
    }
    // 7️⃣7️⃣[X] або [X]7️⃣7️⃣
    else if (r.$1 == r.$2 || r.$2 == r.$3) {
      drawRequest = isNegative 
        ? DrawRequest.casinoNegative2 
        : DrawRequest.casino2;
      reward = JudgeConfig.instance.casinoRewardMedium;
    }
    else {
      drawRequest = isNegative 
        ? DrawRequest.casinoNegative1
        : DrawRequest.casino1;
      reward = JudgeConfig.instance.casinoRewardLow;
    }

    if (jackpot) {
      drawRequest = isNegative ? DrawRequest.casinoAntiJackpot 
                               : DrawRequest.casinoJackpot;
      reward = JudgeConfig.instance.casinoRewardJackpot;
    } else {
      // Додаємо ще рандомне число для більшого азарту.
      // Наприклад, для "🍇🍇🍇" нагорода
      // може бути від 20'001 до 40'000
      reward += Random().nextInt(reward);
    }
  }

  bool _deduceIsNegativeReward((String, String, String) r) =>
      Casino.countBadness(r) > 1;

  bool _randomizeJackpot() {
    var rate = JudgeConfig.instance.casinoJackpotRate;
    if (rate <= 0) rate = 1;
    final r = Random(DateTime.now().millisecond).nextInt(rate);
    return r == 0;
  }
}







class Casino {
  static Future<CommandResult> gambleTelegram(TeleDartMessage message, (String, String, String) r) async {
    // Оновлення або створення користувача
    final (actor, target) = await tg.handleTelegramUserUpdate(message);
    // Викликаємо основну функцію
    return await _handleSlotMachine(actor, r, Platform.telegram);
  }

  static int countBadness((String, String, String) r) {
    // Шукаємо чи є хоч одне емоджі 🅱️ або 🍋 в хоч одній позиції
    // Якщо так, то виграш буде мінусовий
    const badSymbols = ["🅱️", "🍋"];

    // Підрахунок кількості "поганих"
    int badCount = 0;
    if (badSymbols.contains(r.$1)) badCount++;
    if (badSymbols.contains(r.$2)) badCount++;
    if (badSymbols.contains(r.$3)) badCount++;

    return badCount;
  }

  /// Повертає кортеж з емоджі слот машини, наприклад, "🍇", "🍋", "7️⃣".
  /// Всі можливі емоджі в казино: "🅱️", "🍇", "🍋", "7️⃣"
  /// 
  /// Аргумент int дозволяє імплементувати в Discord.
  /// Просте генерування і передача int дозволить отримати винагороду,
  /// але, чи потрібна обмежувати функціонал де користувач не бачить слотів*?
  /// "Слотів" - мається на увазі, що ми приймаємо від користувача
  ///            без анімації :casino:, бо ідея натхненна Telegram
  static Future<(String, String, String)> decode(int diceValue) async {
    int value = diceValue - 1;
    String a, b, c;
    a = casinoEmoji.elementAt(value % 4);
    value = value ~/ 4;
    b = casinoEmoji.elementAt(value % 4);
    value = value ~/ 4;
    c = casinoEmoji.elementAt(value % 4);
    return (a, b, c);
  }

  static Future<bool> _canActorGambleToday(Person actor) async {
    final last = actor.lastUsedCasinoDate;
    if (last == null) return true;

    final diff = DateTime.now().difference(last);
    return diff.inHours >= JudgeConfig.instance.casinoUserCooldownHours;
  }

  static Future<CommandResult> _handleSlotMachine(Person actor, (String, String, String) r, Platform platform) async {
  final bool isActorGambling = await _canActorGambleToday(actor);
    if (!isActorGambling) {
      // Використовуємо останнню дату використаного казино.
      // Якщо дата відсутня ми задаємо поточну дату.
      final fromDate = actor.lastUsedCasinoDate ?? DateTime.now();

      // Тут ми використовуємо останню дату використаного казино і додаємо проміжок часу.
      // В проміжку часу ми встановлюємо параметр "hours",
      // який дорівнює кулдауну в Singleton конфіґ JudgeConfig  
      final toDate = fromDate.add(Duration(hours: JudgeConfig.instance.casinoUserCooldownHours));

      return CommandResult(
        text: '''Ваша остання гра була ${utils.humanReadableDifference(fromDate, DateTime.now())} тому;
Наступна гра через ${utils.humanReadableDifference(DateTime.now(), toDate)}.''',
        deleteBotMessageAfterSeconds: 30
      );
    }

    String? text;
    CasinoResult res = CasinoResult(r);
    if (!res.jackpot) text = "${res.isNegative ? "-" : ""}${res.reward}";

    // Генерація зображення
    await generateUserCasinoImage(actor, res.drawRequest, text ?? "", platform);

    // Відтворення команди
    Iterable<String> args = {res.reward.toString(), ""};
    return CommandResult(text: await submit(actor, r, res.isNegative, args), hasImage: true);
  }

  /// В args очікує першим елементом позитивне число кредитів
  static Future<String> submit(Person actor,
                        (String, String, String) r,
                        bool isNegative, 
                        Iterable<String> args) async {
    final now = DateTime.now();

    // Додаємо комбо або скидуємо комбо
    final lastUsedCasino = actor.lastUsedCasinoDate ?? now;
    final diff = now.difference(lastUsedCasino);
    if (diff.inDays <= 1) {
      actor.casinoStreak++;
    } else {
      actor.casinoStreak = 0;
    }

    // Робимо кулдаун для казино
    actor.lastUsedCasinoDate = now;

    if (isNegative) {
      FuckUp value = await _deduceFuckUpBasedOnBadness(Casino.countBadness(r));
      actor.setFuckUpToday(value);
    }

    // Зберігаємо зміни
    await actor.save();
    
    if (isNegative) {
      // Робимо винагороду негативною якщо переважає 🅱️ або 🍋
      return await credit.SubSocialCredit().execute(actor, actor, args);
    }
    else {
      // Робимо винагороду позитивною якщо переважає 7️⃣ або 🍇
      return await credit.AddSocialCredit().execute(actor, actor, args);
    }
  }

  static Future<FuckUp> _deduceFuckUpBasedOnBadness(int badCount) async {
    // Мапа кількості до рівня
    switch (badCount) {
      case 0: return FuckUp.none;
      case 1: return FuckUp.light;
      case 2: return FuckUp.medium;
      case 3: return FuckUp.fatal; // Якщо три поганих підряд, то це вже критично        
      default: return FuckUp.none;
    }
  }
}