from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

class EnvService:
    def __init__(self):
        self.telegramToken = self.read_api_from_env("TG_BOT_API")
        self.chatgptToken = self.read_api_from_env("OPENAI_API")
        self.telegramBotNickname = self.read_api_from_env("TELEGRAM_BOT_NICKNAME")

    def read_api_from_env(self, env_variable):
        # read variable from environment
        return os.getenv(env_variable)

# Initialize environment service
envService = EnvService()

# Create bot and dispatcher
bot = Bot(token=envService.telegramToken)
dp = Dispatcher()

# Optional: simple check
if __name__ == "__main__":
    print(f"Bot nickname: {envService.telegramBotNickname}")
    print(f"Bot token: {envService.telegramToken[:10]}...")  # partial print for safety
