import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

load_dotenv()

class EnvService:
    def __init__(self):
        # Tokens
        self.discord_token = self.read("DISCORD_TOKEN")
        self.chatgpt_token = self.read("OPENAI_TOKEN")
        self.telegram_token = self.read("TELEGRAM_TOKEN")

        # Owners
        self.telegram_owner_username = self.read("TELEGRAM_OWNER_USERNAME")
        self.discord_owner_username = self.read("DISCORD_OWNER_USERNAME")

        # Misc
        self.data_path = self.read("DATA_PATH")

        # Whitelists
        self.telegram_whitelist = self._parse_whitelist(self.read("WHITELIST_TELEGRAM"))
        self.discord_whitelist = self._parse_whitelist(self.read("WHITELIST_DISCORD"))

    # ---------------------------------------------------------
    # Reading helpers
    # ---------------------------------------------------------
    def read(self, env_variable: str) -> str | None:
        """Read env variable safely."""
        return os.getenv(env_variable)

    def _parse_whitelist(self, raw: str | None) -> list[int]:
        """
        Convert whitelist string like:
          "-123456789;4567890;-789012356;"
        into:
          [-123456789, 4567890, -789012356]

        If raw is None / "null" / "" → return empty list.
        """
        if not raw or raw.lower() == "null":
            return []

        items = raw.split(";")

        whitelist = []
        for item in items:
            item = item.strip()
            if not item:
                continue
            try:
                whitelist.append(int(item))
            except ValueError:
                print(f"[EnvService] WARNING: cannot parse whitelist entry: {item}")

        return whitelist

    # ---------------------------------------------------------
    # Check helpers
    # ---------------------------------------------------------
    def is_telegram_allowed(self, user_id: int) -> bool:
        return user_id in self.telegram_whitelist

    def is_discord_allowed(self, user_id: int) -> bool:
        return user_id in self.discord_whitelist


# Initialize environment service
env = EnvService()

# Create bot and dispatcher
bot = Bot(token=env.telegram_token)
dp = Dispatcher()

if __name__ == "__main__":    
    print("Telegram whitelist:", env.telegram_whitelist)
    print("Discord whitelist:", env.discord_whitelist)

    print("Check TG 123:", env.is_telegram_allowed(123))
    print("Check TG -4885535737:", env.is_telegram_allowed(-4885535737))
