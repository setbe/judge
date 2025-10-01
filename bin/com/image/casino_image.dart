import 'dart:io';
import 'dart:math';

import 'package:image/image.dart' as img;
import 'image.dart';
import '../../person.dart';

Future<String> generateUserCasinoImage(
  Person actor,
  DrawRequest request,
  String text,
  Platform platform,
) async {
  final casinoDir = "data/img/system";
  final systemPath = switch (request) {
    DrawRequest.none => "$casinoDir/1.jpg", // Заглушка
    DrawRequest.casino1 => "$casinoDir/1.jpg",
    DrawRequest.casino2 => "$casinoDir/2.jpg",
    DrawRequest.casino3 => "$casinoDir/3.jpg",
    DrawRequest.casinoNegative1 => "$casinoDir/-1.jpg",
    DrawRequest.casinoNegative2 => "$casinoDir/-2.jpg",
    DrawRequest.casinoNegative3 => "$casinoDir/-3.jpg",
    DrawRequest.casinoJackpot => "$casinoDir/jackpot.jpg",
    DrawRequest.casinoAntiJackpot => "$casinoDir/-jackpot.jpg",
  };

  final userDir = Person.getUserGeneratedImagePath(platform);
  final userPath = "$userDir/${actor.id(platform)}.jpg";
  await Directory(userDir).create(recursive: true);

  // Копіюємо базовий файл
  File(systemPath).copySync(userPath);
  
  final greenColor = img.ColorInt32.rgba(20, 230, 40, 255);
  final redColor   = img.ColorInt32.rgba(234, 13, 23, 255);
  final whiteColor = img.ColorInt32.rgba(255, 255, 255, 255);
  var color = whiteColor;
  switch (request) {
    // Green color
    case DrawRequest.casino1:
    case DrawRequest.casino2:
    case DrawRequest.casino3: color = greenColor;
    break;
    
    // Red color
    case DrawRequest.casinoNegative1:
    case DrawRequest.casinoNegative2:
    case DrawRequest.casinoNegative3: color = redColor;
    break;

    default: color = whiteColor;
    break;
  }

  // Малюємо текст
  const textPos = Point(0.56, 0.36);
  const outlineSize = 5;
  await drawTextOnImage(userPath, userPath, text, textPos, color, outlineSize);

  actor.hasGeneratedImageBySystem = true;
  await actor.save(); // Hive
  return userPath;
}