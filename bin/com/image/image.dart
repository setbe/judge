// image_service.dart
import 'dart:io';
import 'dart:math';
import 'dart:convert'; // для latin1
import 'package:image/image.dart' as img;

// 32-бітний ARGB
int makeColor(int r, int g, int b, [int a = 255]) {
  return (a << 24) | (r << 16) | (g << 8) | b;
}

/// Сервіс роботи з bitmap-шрифтами (згенерованими BMFont)
class Font {
  Font._privateConstructor();
  static final Font _instance = Font._privateConstructor();
  static Font get instance => _instance;

  bool _initialized = false;
  img.BitmapFont? _impactFont;
  late img.BitmapFont _fallbackFont;

  /// Ініціалізація: намагаємось завантажити шрифт `impact` з data/fonts/impact
  Future<void> init() async {
    if (_initialized) return;

    await _loadFonts({"impact", });

    // В якості fallback використовуємо вбудований arial.
    _fallbackFont = img.arial48;
    _initialized = true;
  }

  static Future<Map<String, img.BitmapFont?>> _loadFonts(Iterable<String> fonts) async {
    final Map<String, img.BitmapFont?> map = {}; // ініціалізація

    for (final f in fonts) {
      try {
        map[f] = await _loadFont(f);
        final message = map[f] == null
            ? '[Шрифт!] "$f" НЕ завантажений — використовуємо вбудований.'
            : '[Шрифт] "$f" -> ${map[f]!.characters.length} символів.';
        print(message);
      } catch (e, st) {
        print('[Шрифт!] Не вдалося завантажити "$f": $e\n$st');
        map[f] = null;
      }
    }

    if (map['impact'] != null) {
      Font.instance._impactFont = map['impact'];
    }
    return map;
  }

  /// Завантажує .fnt та відповідний атлас (tga/png). Повертає BitmapFont або null.
  static Future<img.BitmapFont?> _loadFont(String name) async {
    final fontPath = 'data/fonts/$name/';
    final fntFile = File('$fontPath$name.fnt');
    if (!await fntFile.exists()) {
      print('[Font::_loadFont] Файлу ".fnt" НЕ ЗНАЙДЕНО в ${fntFile.path}');
      return null;
    }
    // читаємо як байти, не як String
    final rawStr = await fntFile.readAsString(encoding: utf8);
    // вирізаємо всі рядки з "page id="
    final fntStr = rawStr
    .split('\n')
    .where((line) => !line.trim().startsWith('page '))
    .join('\n');

    String? pagePath;
    final pngPath = '$fontPath${name}_0.png';
    if (await File(pngPath).exists()) {
      pagePath = pngPath;
    }

    if (pagePath == null) {
      print('[Font::_loadFont] No page image found for font "$name" in $fontPath');
      return null;
    }

    final bytes = await File(pagePath).readAsBytes();

    // Спробуємо декодувати Png
    img.Image? pageImage = img.decodePng(bytes);
    if (pageImage == null) {
      print('[Font::_loadFont] Failed to decode page image: $pagePath');
      return null;
    }

    try {
      
      final font = img.BitmapFont.fromFnt(fntStr, pageImage);
      // перевіримо чи є бодай один гліф
      if (font.characters.isEmpty) {
        print('[Font::_loadFont] УВАГА! Завантажений шрифт "$name" МАЄ 0 СИМВОЛІВ.');
      }

      // Після того як font завантажений:
      final keys = font.characters.keys.toList()..sort();
      print('Loaded glyph count: ${keys.length}');
      print('Codes (лише перші п`ятдесят): ${keys.take(50).toList()}');
      // Друк симоволів (може бути великий рядок)
      print('Chars sample (лише перші п`ятдесят): ${keys.map((k)=>String.fromCharCode(k)).take(50).join()}');
      return font;
    } catch (e, st) {
      print('[Font::_loadFont] BitmapFont.fromFnt threw: $e\n$st');
      return null;
    }
  }

  /// Вибір шрифту на основі руни (код-коду символу)
  Future<img.BitmapFont> chooseFont(int rune) async {
    // Переконаємось, що ініціалізація виконана
    if (!_initialized) await init();

    final impact = _impactFont;
    if (impact != null && impact.characters.containsKey(rune)) {
      return impact;
    }
    print("Не знайдено символу ${String.fromCharCode(rune)} в шрифті");
    return _fallbackFont;
  }

  void drawGlyphWithOutline(
    img.Image dst,
    img.BitmapFont font,
    int rune,
    int x,
    int y,
    img.ColorInt32 color,
    int outlineSize) {

  final glyph = font.characters[rune];
  if (glyph == null) return;
  final glyphImg = glyph.image;

  // --- Малюємо контур чорним ---
  final outlineColor = img.ColorInt32.rgb(0, 0, 0);
  for (int oy = -outlineSize; oy <= outlineSize; oy++) {
    for (int ox = -outlineSize; ox <= outlineSize; ox++) {
      if (ox == 0 && oy == 0) continue; // не малюємо основний піксель
      for (int gy = 0; gy < glyphImg.height; gy++) {
        for (int gx = 0; gx < glyphImg.width; gx++) {
          glyphImg.remapChannels(img.ChannelOrder.rgba);
          img.Pixel p = glyphImg.getPixel(gx, gy);
          if (isPixelTransparent(p, color)) continue;
          dst.setPixel(x + gx + glyph.xOffset + ox, y + gy + glyph.yOffset + oy, outlineColor);
        }
      }
    }
  }

  // --- Малюємо сам символ поверх контуру ---
  drawGlyph(dst, font, rune, x, y, color);
}


  void drawGlyph(img.Image dst, img.BitmapFont font, int rune, int x, int y, img.ColorInt32 color) {
    final glyph = font.characters[rune];
    if (glyph == null) return;
    final glyphImg = glyph.image;
  
    for (int gy = 0; gy < glyphImg.height; gy++) {
      for (int gx = 0; gx < glyphImg.width; gx++) {
        glyphImg.remapChannels(img.ChannelOrder.rgba);
        img.Pixel p = glyphImg.getPixel(gx, gy);
        if (isPixelTransparent(p, color)) continue; // прозорі пікселі пропускаємо
        dst.setPixel(x + gx + glyph.xOffset, y + gy + glyph.yOffset, color);
      }
    }
  }

  bool isPixelTransparent(img.Pixel pixel, img.ColorInt32? colorOverlay) {
    img.ColorInt32 color = colorOverlay ?? img.ColorInt32.rgba(0, 0, 0, 0);
    const threshold = 50;
    return
    pixel.r - color.r < threshold &&
    pixel.g - color.g < threshold &&
    pixel.b - color.b < threshold;
  }

  /// Малює текст по-позицiйно, акуратно підсумовуючи xAdvance кожного символа
  Future<void> draw(img.Image dst, String text, Point point, img.ColorInt32 color, int outlineSize) async {
    if (!_initialized) await init();
    if (text.isEmpty) return;
    int x = point.x.toInt();
    final int y = point.y.toInt();

    for (final rune in text.runes) {
      final font = await chooseFont(rune);
      // Малюємо символ
      drawGlyphWithOutline(dst, font, rune, x, y, color, outlineSize);

      // Обчислюємо відступ. Якщо немає конкретного гліфу — беремо приблизний base/2
      final advance = font.characters[rune]?.xAdvance ?? (font.base ~/ 2);
      x += advance + outlineSize*2;
    }
  }
}

/// Запити для системного вибору фону
enum DrawRequest {
  none,
  casino1,
  casino2,
  casino3,
  casinoNegative1,
  casinoNegative2,
  casinoNegative3,
  casinoJackpot,
  casinoAntiJackpot,
}

/// load -> draw -> save
Future<void> drawTextOnImage(String inputPath, String outputPath, String text, Point<double> textPos, img.ColorInt32 color, int outlineSize) async {
  // 1. Завантажуємо PNG/JPG у пам'ять
  final inFile = File(inputPath);
  if (!await inFile.exists()) {
    throw Exception('Input image not found: $inputPath');
  }
  final bytes = await inFile.readAsBytes();
  var image = img.decodeImage(bytes);
  if (image == null) {
    throw Exception('Failed to decode input image: $inputPath');
  }

  // Переконаємось, що шрифти ініціалізовані
  await Font.instance.init();

  
  Point pos = Point(textPos.x * image.width, 
                    textPos.y * image.height);

  // Малюємо текст (await важливий)                  
  await Font.instance.draw(image, text, pos, color, outlineSize);

  // Переконаємось, що директорія існує
  final outFile = File(outputPath);
  await outFile.parent.create(recursive: true);

  // 3. Зберігаємо у новий файл (PNG)
  final encoded = img.encodePng(image);
  await outFile.writeAsBytes(encoded);
}
