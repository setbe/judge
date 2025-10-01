import 'person.dart';
import 'command.dart';
import 'user_repository.dart';


class Judge {
  static const maxTextLength = 128; // Максимальна довжина тексту повідомлення від користувача

  static Future<Command?> findCommand(String name) async {
    final toFind = name.toLowerCase();
    try {
      final cmd = Command.all.firstWhere(
        (cmd) =>
          cmd.name.toLowerCase() == toFind ||
          toFind.startsWith(cmd.slashName)
      );
      return cmd;
    } catch (e) {
      return null;
    }
  }


  static Future<CommandResult> handleCommand(Person person, Person? target, String input) async {
    CommandResult res = CommandResult(text: "", deleteUserMessageAfterSeconds: 5, deleteBotMessageAfterSeconds: 5);
    // Перевірки вхідних даних пункт за пунктом:

    // 1. Занадто довгий текст
    if (input.length > maxTextLength) {
      res.text = "❌ Некоректна команда (>$maxTextLength символів)";
      return res;
    }

    // 2. Розділення на частини
    // Команда має бути мінімум з двох частин: "Суд" "..."
    // (хоч телеграм не дозволить відправити "суд ", бо він замінить це на "суд" без пробілу)
    final parts = input.split(" ");
    final isSlash = input.startsWith("/");
    
    if (!isSlash && parts.length < 2) {
      res.text = "❌ Некоректна команда (< 2 частин)";
      return res;
    }
  
    final cmdName = isSlash ? parts.first.replaceFirst("/", "") :
                              parts.elementAt(1);
    final args = parts.skip(1); // завжди пропускаємо ім'я команди
    final cmd = await findCommand(cmdName);

    // Якщо не знайдено цільового користувача за повідомленням на яке відповідають
    // ми одразу шукаємо за першим аргументом.
    try {
      if (target == null && args.isNotEmpty) {
        target = await UserRepository.instance.findByUsername(args.first, Platform.telegram);
      }
    } catch (e) {
      // Ігноруємо помилку, якщо цілі не знайдено
    }

    // 4. Перевірка існування команди
    if (cmd == null) {
      var status = cmdName;
      if (status.length > 16) {
        status = status.substring(0, 16);
      }
      person.userStatusText = status;
      person.save();
      res.text = "";
      return res;
    }
    // 5. Перевірка прав користувача
    if (person.role.index < cmd.minRole.index) {
      res.text = "❌ У тебе немає прав на цю команду.";
      return res;
    }

    // 6. Виконання команди
    return CommandResult(text: await cmd.execute(person, target, args),
        deleteUserMessageAfterSeconds: cmd.deleteUserMessageAfterSeconds,
        deleteBotMessageAfterSeconds: cmd.deleteBotMessageAfterSeconds,
        hasImage: person.hasGeneratedImageBySystem);
    
  }

  

  
}
