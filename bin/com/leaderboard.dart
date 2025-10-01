import '../person.dart';
import '../command.dart';
import '../user_repository.dart';

class BestLeaderboardCommand extends Command {
  @override
  String get name => "кращі";

  @override
  String get slashName => "highscore";

  @override
  String get description => "Ними пишається партія";

  @override
  int get deleteUserMessageAfterSeconds => 60;

  @override
  int get deleteBotMessageAfterSeconds => 0;

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    final leaders = await UserRepository.instance.getBestLeaders(limit: 15);

    if (leaders.isEmpty) return "Немає даних.";

    final buffer = StringBuffer("🏆 Ними пишається партія:\n");
    for (var i = 0; i < leaders.length; i++) {
      final p = leaders[i];
      buffer.writeln("${i + 1}. ${p.name(null)} — ${p.socialCreditsStr}");
    }

    return buffer.toString();
  }
}

class WorstLeaderboardCommand extends Command {
  @override
  String get name => "гірші";

  @override
  String get slashName => "lowscore";

  @override
  String get description => "Партія розчарована ними";

  @override
  int get deleteUserMessageAfterSeconds => 60;

  @override
  int get deleteBotMessageAfterSeconds => 0;

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    final leaders = await UserRepository.instance.getWorstLeaders(limit: 15);

    if (leaders.isEmpty) return "Немає даних.";

    final buffer = StringBuffer("⬇️👎 Партія розчарована ними:\n");
    for (var i = 0; i < leaders.length; i++) {
      final p = leaders[i];
      buffer.writeln("${i + 1}. ${p.name(null)} — ${p.socialCreditsStr}");
    }

    return buffer.toString();
  }
}