/// Абстрактна клавіатура
abstract class Keyboard {
  /// Повертає структуру кнопок у вигляді платформо-незалежної моделі
  List<List<Button>> get layout;
}

/// Абстрактна кнопка
class Button {
  final String text;
  final String callbackData;

  Button(this.text, this.callbackData);
}

/// Конкретна реалізація для Telegram
class TelegramKeyboard extends Keyboard {
  final List<List<Button>> _layout;

  TelegramKeyboard(this._layout);

  @override
  List<List<Button>> get layout => _layout;

  /// Перетворення у формат, який розуміє Telegram API
  List<List<Map<String, String>>> toTelegramFormat() {
    return _layout
        .map((row) => row
            .map((btn) => {
                  "text": btn.text,
                  "callback_data": btn.callbackData,
                })
            .toList())
        .toList();
  }
}

/// (Майбутня) реалізація для Discord
class DiscordKeyboard extends Keyboard {
  final List<List<Button>> _layout;

  DiscordKeyboard(this._layout);

  @override
  List<List<Button>> get layout => _layout;

  // Тут буде специфічна реалізація під Discord
}
