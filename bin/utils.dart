/// Returns human-readable difference string between two DateTimes.
/// Examples:
///  "0 с", "59 с", "1 хв", "58 хв", "1 год 1 хв", "1 доба 13 год", "2 доби 3 год"
String humanReadableDifference(DateTime from, DateTime to) {
  final diff = to.difference(from).inSeconds.abs();

  final days = diff ~/ 86400;
  final hours = (diff % 86400) ~/ 3600;
  final minutes = (diff % 3600) ~/ 60;
  final seconds = diff % 60;

  if (diff < 60) {
    return "$seconds с";
  }

  final parts = <String>[];
  if (days > 0) parts.add("$days ${days == 1 ? "доба" : "доби"}");
  if (hours > 0) parts.add("$hours год");
  if (minutes > 0) parts.add("$minutes хв");

  return parts.join(" ");
}