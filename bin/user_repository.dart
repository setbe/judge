import 'package:hive/hive.dart';

import 'dart:io';
import 'dart:convert';

import 'env_service.dart';
import 'person.dart';
import 'person_json.dart';

/// Singleton репозиторій користувачів
class UserRepository {
  UserRepository._internal(); // private constructor
  static final UserRepository instance = UserRepository._internal();

  late Box<Person> _box;

  Future<void> init() async {
    Hive.registerAdapter(PersonAdapter());
    Hive.registerAdapter(RoleAdapter());
    Hive.registerAdapter(UserStateAdapter());
    Hive.registerAdapter(PlatformAdapter());
    Hive.registerAdapter(FuckUpAdapter());
    _box = await Hive.openBox<Person>('users');

    // --- load from user.json if exists ---
    final file = File('data/user.json');
    if (await file.exists()) {
      final raw = await file.readAsString();
      final List<dynamic> jsonList = jsonDecode(raw);

      for (final entry in jsonList) {
        final user = PersonJson.fromJson(entry);
        final key = user.telegramId ?? user.discordId;
        if (key != null) {
          await _box.put(key, user); // додаємо або оновлюємо
        }
      }
    }
  }

  Future<bool> hasUserGeneratedImageByUserId(int id, Platform platform) async {
    var user = _box.get(id);
    if (user == null) return false;

    return false;
  }

  Future<Person> getOrCreateTelegramUser(int telegramId, String name, String username) async {
    final ownerUsername = EnvService.instance.ownerUsername(Platform.telegram);

    var user = _box.get(telegramId);
    if (user == null) {
      final role = (username == ownerUsername)
          ? Role.admin : Role.user;
      user = Person(
          id:       telegramId,
          name:     name,
          username: username,
          role:     role,
          platform: Platform.telegram);
      await _box.put(telegramId, user);
    }
    return user;
  }

  Future<void> updateUser(Person p) async {
    final key = p.telegramId ?? p.discordId;
    if (key != null) {
      await _box.put(key, p);
    }
  }

  /// Знаходить користувача за username і платформою
  /// username може бути "user" або "@user"
  Future<Person?> findByUsername(String username, Platform platform) async {
    final clean = username.startsWith('@') ? username.substring(1) : username;

    for (final person in _box.values) {
      if (platform == Platform.telegram && person.telegramUsername == clean) return person;
      if (platform == Platform.discord && person.discordUsername == clean) return person;
    }
    return null;
  }

}

extension Leaderboards on UserRepository {
  Future<List<Person>> getBestLeaders({int limit = 15}) async {
    final users = _box.values
      .where((u) => u.socialCredits < 1000100170) // пропускаємо завеликі
      .toList();
    users.sort((a, b) => b.socialCredits.compareTo(a.socialCredits));
    return users.take(limit).toList();
  }

  Future<List<Person>> getWorstLeaders({int limit = 15}) async {
    final users = _box.values.toList();
    users.sort((a, b) => a.socialCredits.compareTo(b.socialCredits));
    return users.take(limit).toList();
  }
}