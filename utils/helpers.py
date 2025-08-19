import base64
import asyncio
from datetime import datetime, timedelta
import re

class BotHelpers:
    @staticmethod
    def generate_referral_link(user_id, bot_username):
        """Generate unique referral link for user"""
        encoded_id = base64.b64encode(str(user_id).encode()).decode()
        return f"https://t.me/{bot_username}?start=ref_{encoded_id}"
    
    @staticmethod
    def decode_referral_id(ref_code):
        """Decode referral ID from start parameter"""
        try:
            if ref_code.startswith('ref_'):
                encoded_id = ref_code[4:]
                return int(base64.b64decode(encoded_id.encode()).decode())
        except:
            return None
        return None
    
    @staticmethod
    def format_number(number):
        """Format number with Persian separators"""
        return f"{number:,}".replace(',', '،')
    
    @staticmethod
    def get_user_rank_emoji(rank):
        """Get emoji for user rank"""
        if rank == 1:
            return "🥇"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        elif rank <= 10:
            return "🏆"
        else:
            return "👤"
    
    @staticmethod
    def validate_channel_id(channel_id):
        """Validate channel ID format"""
        pattern = r'^@[a-zA-Z][a-zA-Z0-9_]{4,31}$'
        return bool(re.match(pattern, channel_id))
    
    @staticmethod
    def format_datetime(dt_string):
        """Format datetime string to Persian"""
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime('%Y/%m/%d - %H:%M')
        except:
            return dt_string
    
    @staticmethod
    def calculate_user_level(points):
        """Calculate user level based on points"""
        if points < 50:
            return "مبتدی", "🌱"
        elif points < 100:
            return "برنزی", "🥉"
        elif points < 200:
            return "نقره‌ای", "🥈"
        elif points < 500:
            return "طلایی", "🥇"
        elif points < 1000:
            return "پلاتینی", "💎"
        else:
            return "الماسی", "💠"
    
    @staticmethod
    async def safe_send_message(bot, user_id, text, **kwargs):
        """Safely send message to user"""
        try:
            return await bot.send_message(user_id, text, **kwargs)
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
            return None
    
    @staticmethod
    async def safe_edit_message(message, text, **kwargs):
        """Safely edit message"""
        try:
            return await message.edit_text(text, **kwargs)
        except Exception as e:
            print(f"Failed to edit message: {e}")
            return None
    
    @staticmethod
    def get_file_type(file):
        """Determine file type from Telegram file object"""
        if hasattr(file, 'photo'):
            return 'photo'
        elif hasattr(file, 'video'):
            return 'video'
        elif hasattr(file, 'document'):
            return 'document'
        elif hasattr(file, 'audio'):
            return 'audio'
        elif hasattr(file, 'voice'):
            return 'voice'
        elif hasattr(file, 'animation'):
            return 'animation'
        else:
            return 'unknown'
    
    @staticmethod
    def truncate_text(text, max_length=100):
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def is_valid_user_id(user_id):
        """Check if user ID is valid"""
        try:
            user_id = int(user_id)
            return 0 < user_id < 10**10
        except:
            return False