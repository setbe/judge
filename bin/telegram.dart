import 'package:hive/hive.dart';

// Пакети для роботи з Telegram API та середовищем
import 'package:teledart/model.dart';
import 'package:teledart/teledart.dart';
import 'package:teledart/telegram.dart';

import 'env_service.dart';
import 'casino.dart';

import 'command.dart';
import 'user_repository.dart';
import 'person.dart';

import 'judge.dart'; // for `Judge`
import 'config.dart'; // JudgeConfig
import 'com/image/image.dart' as myimg;

import 'dart:io' as io;

late final String botTelegramToken; // Токен бота

/// Перевірка на "Суд " з ігнором регістру
  bool _hasJudgePrefix(String text) => text.toLowerCase().startsWith("суд ");

Future<void> init() async {
  JudgeConfig.instance.init();
  // 1. Ініціалізація env та отримання токена бота
  try {
    await EnvService.instance.init(envPaths: ['.env']); 
    botTelegramToken = EnvService.instance.getBotToken(Platform.telegram);
  } catch (e) {
    print(e); // Помилка завантаження токена
    return; // Завершення ініціалізації з помилкою
  }

  // 2. Ініціалізація репозиторію користувачів та Hive
  Hive.init('data');
  await UserRepository.instance.init();
  await myimg.Font.instance.init();

  // 3. Ініціалізація Telegram бота
  var telegram = Telegram(botTelegramToken);
  var me = await telegram.getMe();
  var teledart = TeleDart(botTelegramToken, Event(me.username!));
  print("✅ Бот запущений як @${me.username}");
  teledart.start();

  // 4. Реєстрація обробників подій Telegram
  _registerTelegramHandlers(teledart);
} // init

Future<(Person, Person?)> handleTelegramUserUpdate(
  TeleDartMessage message,
) async {
  final user = message.from;
  if (user == null) {
    throw Exception("Немає інформації про користувача");
  }

  // Реєстрація користувача або отримання існуючого
  final person = await UserRepository.instance.getOrCreateTelegramUser(
    user.id,
    user.firstName,
    user.username ?? "без_нікнейму",
  );
  // Оновлення імені та нікнейму на випадок зміни
  person.telegramName = user.firstName;
  person.telegramUsername = user.username ?? "без_нікнейму";
  if (person.username(Platform.telegram) == EnvService.instance.ownerUsername(Platform.telegram)) {
    person.role = Role.admin; // Видача адміна за ENV змінною
  }
  person.save();

  // Отримання цільового користувача, якщо це відповідь на повідомлення
  Person? target;
  if (message.replyToMessage != null && message.replyToMessage!.from != null) {
    final replyUser = message.replyToMessage!.from!;
    target = await UserRepository.instance.getOrCreateTelegramUser(
      replyUser.id,
      replyUser.firstName,
      replyUser.username ?? "без_нікнейму",
    );
    // Оновлення імені та нікнейму на випадок зміни
    target.telegramName = replyUser.firstName;
    target.telegramUsername = replyUser.username ?? "без_нікнейму";
    await UserRepository.instance.updateUser(target);
  } else {
    target = null;
  }
  return (person, target);
}

/// Реєстрація обробників подій Telegram
Future<void> _registerTelegramHandlers(TeleDart teledart) async {
  teledart.onMessage().listen((message) async {
    // Якщо айді чату не в білому списку, ми ігноруємо повідомлення
    if (!EnvService.instance.inWhitelist(message.chat.id, Platform.telegram)) {
      return;
    }
    // Оновлення або створення користувача
    var (person, target) = await handleTelegramUserUpdate(message);

    // Обробка текстових повідомлень
    final text = message.text ?? "";

    CommandResult res = CommandResult(text: "");
    if (_hasJudgePrefix(text)) {
      res = await Judge.handleCommand(person, target, text);
    } else {
      // Не команда "Суд ", ігноруємо всі команди, але якщо повідомлення містить
      // щось інше (прикріплення: фото..., дії...) — обробляємо його тут:

      // 1. Дайси
      final diceRes = await _handleDice(message);
      if (diceRes != null) res = diceRes;
    }

    if (res.text.isEmpty) return;

    // Цей рядок милиця, але дуже зручно.
    if (res.text.startsWith("===== Person Debug =====")) res.text += "\nchat ID: ${message.chat.id}";
    
    Message? botMsg;
    // Реєструємо зображення з команди і надсилаємо його користувачеві
    if (res.hasImage) {
      final path = person.pollLastGeneratedImage;
      if (path != null) {
        botMsg = await teledart.sendPhoto(message.chat.id, io.File(path), caption: res.text);
      }
    } else {
      botMsg = await teledart.sendMessage(message.chat.id, res.text);
    }
    
    if (botMsg != null) {
      await _deleteTelegramMessagesDelayed(teledart, res, botMsg, message);
    }
  });
} // registerTelegramHandlers

Future<void> _deleteTelegramMessagesDelayed(TeleDart teledart, CommandResult res, Message botMsg, TeleDartMessage message) async {
  // якщо треба – плануємо видалення
  final botMsgLifetime = res.deleteBotMessageAfterSeconds;
  final userMsgLifetime = res.deleteUserMessageAfterSeconds;
  if (botMsgLifetime > 0) {
    final Duration durBot = (botMsgLifetime == 1)
      ? Duration(seconds: 0) 
      : Duration(seconds: botMsgLifetime);
    Future.delayed(durBot, (){ teledart.deleteMessage(botMsg.chat.id, botMsg.messageId); });
  }
  if (userMsgLifetime > 0) {
    final Duration durUser = (userMsgLifetime == 1) 
      ? Duration(seconds: 0) 
      : Duration(seconds: userMsgLifetime);
    Future.delayed(durUser, (){ teledart.deleteMessage(message.chat.id, message.messageId); });
  }
}

/// Обробка повідомлень з дайсом (кубиком, слот-машиною...)
Future<CommandResult?> _handleDice(TeleDartMessage message) async {
  // (https://core.telegram.org/bots/api#dice)
  // Перевіряємо об'єкт Dice з повідомлення.
  final dice = message.dice;
  if (dice == null) return null;

  // Шукаємо, чи є це "дайс" казино (слот-машина)
  if (dice.emoji.compareTo(Dice.emojiSlotMachine) == 0) {
    return await Casino.gambleTelegram(
          message,
          await Casino.decode(dice.value),
          ); 
  }
  return null;
}
