from memory.long_term_memory import get_recent_mood


class DataMonitor:
    def __init__(self):
        self._last_check = None

    def check(self) -> list[dict]:
        anomalies = []
        anomalies.extend(self._check_mood_trend())
        return anomalies

    def _check_mood_trend(self) -> list[dict]:
        recent = get_recent_mood(7)
        if len(recent) < 3:
            return []

        negative_moods = {"anxious", "sad", "frustrated", "angry", "tired"}
        negative_count = sum(1 for r in recent if r.get("mood", "") in negative_moods)

        if negative_count >= 3:
            return [{
                "source": "mood_trend",
                "severity": "warning",
                "message": f"Recent {negative_count}/{len(recent)} mood entries are negative"
            }]

        return []

    def get_mood_summary(self) -> str:
        recent = get_recent_mood(5)
        if not recent:
            return "no mood data"

        moods = [r.get("mood", "neutral") for r in recent]
        most_recent = moods[-1] if moods else "neutral"

        negative = {"anxious", "sad", "frustrated", "angry", "tired"}
        trend = "declining" if sum(1 for m in moods if m in negative) >= 3 else "stable"

        return f"Most recent mood: {most_recent}, trend: {trend}"
