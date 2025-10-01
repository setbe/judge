import '../person.dart';
import '../command.dart';

class WhoAmICommand extends Command {
  @override
  String get name => "я";

  @override
  String get slashName => "i";

  @override
  String get description => "Інформація про тебе";

  @override
  int get deleteUserMessageAfterSeconds => 30; // повідомлення видаляється через 30 секунд

  @override
  int get deleteBotMessageAfterSeconds => 0;

  

  @override
  Future<String> execute(Person actor, Person? target, Iterable<String> args) async {
    Person person = target ?? actor;
    return await executeFor(person, person.socialCreditsStr);
  }

  static Future<String> executeFor(Person actor, String socialCredits) async {
    String actorRole = '';
    switch (actor.role) {
      case Role.moder: actorRole = "⛑"; break;
      case Role.admin: actorRole = "⚿"; break;
      default: actorRole = ''; break;
    }

    String socialNotice = actor.lastSocialCreditNotice ?? "";
    if (socialNotice.isNotEmpty) socialNotice += "⚬ замітка: $socialNotice";
    
    // перевірка серії факапів
    final fuckUpStreak = _countFuckUpStreak(actor.fuckUpsPerWeek);
    if (fuckUpStreak >= 4) {
      socialNotice += "${socialNotice.isNotEmpty ? "\n" : ""}⚠️ ${actor.name(null)} виставляє Партію Платона в негативному руслі вже $fuckUpStreak днів підряд";
    }

    String gamblingNotice = await getGamblingNotice(actor.casinoStreak);
    if (gamblingNotice.isNotEmpty) {
      final streakNotice = "${actor.casinoStreak} крут"
          "${actor.casinoStreak == 1 ? "ка"
           : actor.casinoStreak < 5 ? "ки" : "ок"}"
          " підряд";
      gamblingNotice = "⚬ $gamblingNotice${gamblingNotice.startsWith("лудоман") ? "" : ": $streakNotice"}";
    }

    String notices = socialNotice + gamblingNotice;

    return
"""
${actor.userStatusText ?? ""} ${actor.name(null)} $actorRole
⚬ соц. кредити: $socialCredits 
$notices
""";
  } // executeFor

  static Future<String> getGamblingNotice(int casinoStreak) async {
    switch (casinoStreak) {
      case 0: return "";
      case 1: return "";
      case 2: return "ризикант";
      case 3: return "cлотогеймер";  
      case 4: return "азартний ставочник"; 
      case 5: return "шанувальник казино";
      case 6: return "профі-беттор";
      case 7: return "ризиковий інвестор";
      case 8: return "ловець джекпоту";
      default: return "лудоман $casinoStreak рівня";
    }
  }

  
  /// Рахує максимальну довжину підрядних днів із fuckup != none
  static int _countFuckUpStreak(List<FuckUp> week) {
    int streak = 0;
    int current = 0;
    for (var f in week) {
      if (f != FuckUp.none) {
        current++;
        streak = current > streak ? current : streak;
      } else {
        current = 0;
      }
    }
    return streak;
  }
}

