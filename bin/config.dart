/// Sigleton сервіс для роботи з конфіґом
class JudgeConfig {
  JudgeConfig._privateConstructor();
  static final JudgeConfig _instance = JudgeConfig._privateConstructor();
  static JudgeConfig get instance => _instance;
  bool _initialized = false;

  /// Після днів, коли "забувається" соціальна замітка
  late int _daysToForgetUserNotice;

  /// Константа для визначення низької пенальті
  late int _fuckUpSocialCreditsPenaltyK1;
  /// Константа для визначення середньої пенальті
  late int _fuckUpSocialCreditsPenaltyK10;
  /// Константа для визначення високої пенальті
  late int _fuckUpSocialCreditsPenaltyK100;

  /// Джекпот
  late int _casinoRewardJackpot;
  /// Найбільша нагорода (не враховуючи джекпот)
  late int _casinoRewardHigh;
  /// Середня нагорода
  late int _casinoRewardMedium; 
  /// Мінімальна нагорода
  late int _casinoRewardLow;
  /// Кулдаун в годинах для казино
  late int _casinoUserCooldownHours;
  /// Використовується як параметр для NextInt. Якщо NextInt дає 0, це означає джекпот
  late int _casinoJackpotRate;


  // TODO: Серіалізація даних щоб змінювати значення в телеграм/дискорд
  Future<void> init() async {
    if (_initialized) return;
    
    _daysToForgetUserNotice = 2;
    _fuckUpSocialCreditsPenaltyK1   = 1000;
    _fuckUpSocialCreditsPenaltyK10  = 10000;
    _fuckUpSocialCreditsPenaltyK100 = 100000;
    _casinoRewardJackpot = 100000;
    _casinoRewardHigh   = 20000;
    _casinoRewardMedium = 7500;
    _casinoRewardLow    = 1000;
    _casinoUserCooldownHours = 20;
    _casinoJackpotRate = 10;

    _initialized = true;
  }

  get daysToForgetUserNotice {
    if (!_initialized) throw Exception('JudgeConfig не ініціалізований');
    return _daysToForgetUserNotice;
  }

  get fuckUpSocialCreditsPenaltyK1 => _fuckUpSocialCreditsPenaltyK1;
  get fuckUpSocialCreditsPenaltyK10 => _fuckUpSocialCreditsPenaltyK10;
  get fuckUpSocialCreditsPenaltyK100 => _fuckUpSocialCreditsPenaltyK100;

  get casinoRewardJackpot => _casinoRewardJackpot;
  get casinoRewardHigh => _casinoRewardHigh;
  get casinoRewardMedium => _casinoRewardMedium;
  get casinoRewardLow => _casinoRewardLow;
  get casinoUserCooldownHours => _casinoUserCooldownHours;
  get casinoJackpotRate => _casinoJackpotRate;
  
}