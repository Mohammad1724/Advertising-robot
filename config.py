import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot.db')

# Bot Settings
REFERRAL_REWARD = int(os.getenv('REFERRAL_REWARD', 10))
MIN_REFERRALS_FOR_CONTENT = int(os.getenv('MIN_REFERRALS_FOR_CONTENT', 5))
BROADCAST_DELAY = float(os.getenv('BROADCAST_DELAY', 0.1))

# Campaign Settings
MAX_CAMPAIGN_SIZE = int(os.getenv('MAX_CAMPAIGN_SIZE', 10000))
AB_TEST_MIN_SIZE = int(os.getenv('AB_TEST_MIN_SIZE', 100))
CAMPAIGN_TIMEOUT = int(os.getenv('CAMPAIGN_TIMEOUT', 3600))

# Analytics Settings
ANALYTICS_RETENTION_DAYS = int(os.getenv('ANALYTICS_RETENTION_DAYS', 90))
REPORT_FREQUENCY_HOURS = int(os.getenv('REPORT_FREQUENCY_HOURS', 24))

# Security Settings
MAX_MESSAGES_PER_MINUTE = int(os.getenv('MAX_MESSAGES_PER_MINUTE', 30))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))

# Feature Flags
ENABLE_AB_TESTING = os.getenv('ENABLE_AB_TESTING', 'true').lower() == 'true'
ENABLE_CROSS_PROMOTION = os.getenv('ENABLE_CROSS_PROMOTION', 'true').lower() == 'true'
ENABLE_SMART_TARGETING = os.getenv('ENABLE_SMART_TARGETING', 'true').lower() == 'true'
ENABLE_AUTO_OPTIMIZATION = os.getenv('ENABLE_AUTO_OPTIMIZATION', 'true').lower() == 'true'

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', 10485760))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))