import 'person.dart';

extension PersonJson on Person {
  static Person fromJson(Map<String, dynamic> json) {
    return Person(
      id: json["telegramId"] ?? json["discordId"],
      name: json["telegramName"] ?? json["discordName"],
      username: json["telegramUsername"] ?? json["discordUsername"],
      platform: _parsePlatform(json["platform"]),
      role: _parseRole(json["role"]),
      other: (json["other"] as Map?)?.cast<String, dynamic>(),
      socialCredits: json["_socialCredits"] ?? 0,
      state: _parseState(json["state"]),
      dailySocialCreditsLeft: json["dailySocialCreditsLeft"] ?? 5000,
      dailySocialCreditsLimit: json["dailySocialCreditsLimit"] ?? 5000,
      hasGeneratedImageBySystem: json["hasGeneratedImageBySystem"] ?? false,
      fuckUpsPerWeek: (json["fuckUpsPerWeek"] as List?)
          ?.map((e) => _parseFuckUp(e))
          .toList(),
    )
      ..telegramId = json["telegramId"]
      ..telegramName = json["telegramName"]
      ..telegramUsername = json["telegramUsername"]
      ..discordId = json["discordId"]
      ..discordName = json["discordName"]
      ..discordUsername = json["discordUsername"]
      ..lastUsedCasinoDate = _parseDate(json["lastUsedCasinoDate"])
      ..lastUsedPersonaDate = _parseDate(json["lastUsedPersonaDate"])
      ..userStatusText = json["userStatusText"]
      ..casinoStreak = json["casinoStreak"] ?? 0;
  }

  // =====================
  // helpers
  // =====================

  static Role _parseRole(dynamic v) {
    if (v is int) return Role.values[v];
    if (v is String) {
      return Role.values.firstWhere( 
        (e)        => e.name == v, 
        orElse: () => Role.user);
    }
    return Role.user;
  }

  static UserState _parseState(dynamic v) {
    if (v is int) return UserState.values[v];
    if (v is String) {
      return UserState.values.firstWhere(
        (e) => e.name == v,
        orElse: () => UserState.neutral);
    }
    return UserState.neutral;
  }

  static Platform? _parsePlatform(dynamic v) {
    if (v == null) return null;
    if (v is int) return Platform.values[v];
    if (v is String) {
      return Platform.values.firstWhere(
        (e) => e.name == v,
        orElse: () => Platform.telegram);
    }
    return null;
  }

  static FuckUp _parseFuckUp(dynamic v) {
    if (v is int) return FuckUp.values[v];
    if (v is String) {
      return FuckUp.values.firstWhere(
        (e) => e.name == v,
        orElse: () => FuckUp.none);
    }
    return FuckUp.none;
  }

  static DateTime? _parseDate(dynamic v) {
    if (v == null) return null;
    if (v is String) return DateTime.tryParse(v);
    if (v is int) return DateTime.fromMillisecondsSinceEpoch(v);
    return null;
  }
}
