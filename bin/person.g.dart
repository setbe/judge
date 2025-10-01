// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'person.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class PersonAdapter extends TypeAdapter<Person> {
  @override
  final int typeId = 1;

  @override
  Person read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return Person(
      role: fields[3] as Role,
      other: (fields[4] as Map?)?.cast<String, dynamic>(),
      state: fields[9] as UserState,
      hasGeneratedImageBySystem: fields[16] as bool,
    )
      ..telegramId = fields[0] as int?
      ..telegramName = fields[1] as String?
      ..telegramUsername = fields[2] as String?
      ..discordId = fields[5] as int?
      ..discordName = fields[6] as String?
      ..discordUsername = fields[7] as String?
      .._socialCredits = fields[8] as int
      .._lastSocialCreditNotice = fields[10] as String?
      .._lastSocialCreditNoticeDate = fields[11] as DateTime?
      .._dailySocialCreditsLeft = fields[12] as int
      .._dailySocialCreditsLimit = fields[13] as int
      ..lastUsedCasinoDate = fields[14] as DateTime?
      ..lastUsedPersonaDate = fields[15] as DateTime?
      .._fuckUpsPerWeek = (fields[17] as List).cast<FuckUp>()
      ..userStatusText = fields[18] as String?
      ..casinoStreak = fields[19] as int;
  }

  @override
  void write(BinaryWriter writer, Person obj) {
    writer
      ..writeByte(20)
      ..writeByte(0)
      ..write(obj.telegramId)
      ..writeByte(1)
      ..write(obj.telegramName)
      ..writeByte(2)
      ..write(obj.telegramUsername)
      ..writeByte(3)
      ..write(obj.role)
      ..writeByte(4)
      ..write(obj.other)
      ..writeByte(5)
      ..write(obj.discordId)
      ..writeByte(6)
      ..write(obj.discordName)
      ..writeByte(7)
      ..write(obj.discordUsername)
      ..writeByte(8)
      ..write(obj._socialCredits)
      ..writeByte(9)
      ..write(obj.state)
      ..writeByte(10)
      ..write(obj._lastSocialCreditNotice)
      ..writeByte(11)
      ..write(obj._lastSocialCreditNoticeDate)
      ..writeByte(12)
      ..write(obj._dailySocialCreditsLeft)
      ..writeByte(13)
      ..write(obj._dailySocialCreditsLimit)
      ..writeByte(14)
      ..write(obj.lastUsedCasinoDate)
      ..writeByte(15)
      ..write(obj.lastUsedPersonaDate)
      ..writeByte(16)
      ..write(obj.hasGeneratedImageBySystem)
      ..writeByte(17)
      ..write(obj._fuckUpsPerWeek)
      ..writeByte(18)
      ..write(obj.userStatusText)
      ..writeByte(19)
      ..write(obj.casinoStreak);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is PersonAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class RoleAdapter extends TypeAdapter<Role> {
  @override
  final int typeId = 0;

  @override
  Role read(BinaryReader reader) {
    switch (reader.readByte()) {
      case 0:
        return Role.user;
      case 1:
        return Role.moder;
      case 2:
        return Role.admin;
      default:
        return Role.user;
    }
  }

  @override
  void write(BinaryWriter writer, Role obj) {
    switch (obj) {
      case Role.user:
        writer.writeByte(0);
        break;
      case Role.moder:
        writer.writeByte(1);
        break;
      case Role.admin:
        writer.writeByte(2);
        break;
    }
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is RoleAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class UserStateAdapter extends TypeAdapter<UserState> {
  @override
  final int typeId = 2;

  @override
  UserState read(BinaryReader reader) {
    switch (reader.readByte()) {
      case 0:
        return UserState.neutral;
      case 1:
        return UserState.good;
      case 2:
        return UserState.bad;
      default:
        return UserState.neutral;
    }
  }

  @override
  void write(BinaryWriter writer, UserState obj) {
    switch (obj) {
      case UserState.neutral:
        writer.writeByte(0);
        break;
      case UserState.good:
        writer.writeByte(1);
        break;
      case UserState.bad:
        writer.writeByte(2);
        break;
    }
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserStateAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class PlatformAdapter extends TypeAdapter<Platform> {
  @override
  final int typeId = 3;

  @override
  Platform read(BinaryReader reader) {
    switch (reader.readByte()) {
      case 0:
        return Platform.telegram;
      case 1:
        return Platform.discord;
      default:
        return Platform.telegram;
    }
  }

  @override
  void write(BinaryWriter writer, Platform obj) {
    switch (obj) {
      case Platform.telegram:
        writer.writeByte(0);
        break;
      case Platform.discord:
        writer.writeByte(1);
        break;
    }
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is PlatformAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class FuckUpAdapter extends TypeAdapter<FuckUp> {
  @override
  final int typeId = 4;

  @override
  FuckUp read(BinaryReader reader) {
    switch (reader.readByte()) {
      case 0:
        return FuckUp.none;
      case 1:
        return FuckUp.light;
      case 2:
        return FuckUp.medium;
      case 3:
        return FuckUp.high;
      case 4:
        return FuckUp.fatal;
      default:
        return FuckUp.none;
    }
  }

  @override
  void write(BinaryWriter writer, FuckUp obj) {
    switch (obj) {
      case FuckUp.none:
        writer.writeByte(0);
        break;
      case FuckUp.light:
        writer.writeByte(1);
        break;
      case FuckUp.medium:
        writer.writeByte(2);
        break;
      case FuckUp.high:
        writer.writeByte(3);
        break;
      case FuckUp.fatal:
        writer.writeByte(4);
        break;
    }
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is FuckUpAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
