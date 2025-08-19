import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# Import configurations and handlers
from config import BOT_TOKEN, CHANNEL_ID, ADMIN_ID
from database.models import Database
from handlers.user_handlers import UserHandlers
from handlers.referral_handlers import ReferralHandlers
from handlers.admin_handlers import AdminHandlers
from utils.scheduler import BotScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Initialize database and handlers
db = Database()
user_handlers = UserHandlers(bot, db)
referral_handlers = ReferralHandlers(bot, db)
admin_handlers = AdminHandlers(bot, db, ADMIN_ID)
scheduler = BotScheduler(bot, db)

# Register handlers
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await user_handlers.start_command(message)

@dp.message_handler(commands=['admin'])
async def admin_command(message: types.Message):
    await admin_handlers.show_admin_panel(message)

@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await admin_handlers.send_quick_stats(message)
    else:
        await message.answer("❌ شما دسترسی به این دستور ندارید!")

@dp.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'animation'])
async def handle_messages(message: types.Message):
    # Handle admin messages (like broadcast creation)
    await admin_handlers.handle_admin_message(message)

@dp.callback_query_handler()
async def handle_callback_queries(callback: types.CallbackQuery):
    # Route callback queries to appropriate handlers
    if callback.data.startswith(('admin_', 'broadcast_')):
        await admin_handlers.handle_callback_query(callback)
    elif callback.data.startswith(('referral_', 'my_referrals', 'claim_reward', 'copy_link')):
        await referral_handlers.handle_callback_query(callback)
    else:
        await user_handlers.handle_callback_query(callback)

# Startup and shutdown events
async def on_startup(dp):
    """Initialize bot on startup"""
    logging.info("Bot is starting up...")
    
    # Initialize database
    await db.init_db()
    logging.info("Database initialized")
    
    # Start scheduler
    scheduler.start()
    logging.info("Scheduler started")
    
    # Send startup notification to admin
    try:
        await bot.send_message(
            ADMIN_ID,
            "🚀 ربات با موفقیت راه‌اندازی شد!\n\n"
            f"⏰ زمان شروع: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n"
            "✅ تمام سیستم‌ها آماده هستند."
        )
    except Exception as e:
        logging.error(f"Failed to send startup notification: {e}")

async def on_shutdown(dp):
    """Cleanup on shutdown"""
    logging.info("Bot is shutting down...")
    
    # Stop scheduler
    scheduler.stop()
    logging.info("Scheduler stopped")
    
    # Send shutdown notification to admin
    try:
        await bot.send_message(
            ADMIN_ID,
            "⏹ ربات متوقف شد.\n\n"
            f"⏰ زمان توقف: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}"
        )
    except Exception as e:
        logging.error(f"Failed to send shutdown notification: {e}")

if __name__ == '__main__':
    logging.info("Starting Telegram Channel Bot...")
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )