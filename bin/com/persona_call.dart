import '../person.dart';
import '../command.dart';

class PersonaCallCommand extends Command {
  @override
  String get name => "🔫";

  @override
  String get slashName => "🔫";

  @override
  String get description => "Інформація про тебе";

  @override
  int get deleteUserMessageAfterSeconds => 30; // повідомлення видаляється через 30 секунд

  @override
  int get deleteBotMessageAfterSeconds => 30; // повідомлення видаляється через 30 секунд

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    return "тут буде нічний виклик";
  }
}