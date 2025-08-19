import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Bot settings
REFERRAL_REWARD = 10  # Points per referral
MIN_REFERRALS_FOR_CONTENT = 5
BROADCAST_DELAY = 1  # Seconds between messages

# Database settings
DATABASE_PATH = "bot.db"