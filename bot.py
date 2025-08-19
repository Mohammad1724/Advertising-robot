import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import BotCommand

# Import configurations and handlers
from config import BOT_TOKEN, CHANNEL_ID, ADMIN_ID
from database.models import Database
from handlers.user_handlers import UserHandlers
from handlers.referral_handlers import ReferralHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.advertising_handlers import AdvertisingHandlers
from utils.scheduler import BotScheduler
from utils.campaign_manager import CampaignManager
from utils.ab_testing import ABTestManager
from utils.analytics import Analytics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Initialize database and handlers
db = Database()
user_handlers = UserHandlers(bot, db)
referral_handlers = ReferralHandlers(bot, db)
admin_handlers = AdminHandlers(bot, db, ADMIN_ID)
advertising_handlers = AdvertisingHandlers(bot, db)

# Initialize utilities
scheduler = BotScheduler(bot, db)
campaign_manager = CampaignManager(bot, db)
ab_test_manager = ABTestManager(bot, db)
analytics = Analytics(db)

# ==================== COMMAND HANDLERS ====================

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """Handle /start command"""
    try:
        await user_handlers.start_command(message)
        logger.info(f"User {message.from_user.id} started the bot")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

@dp.message_handler(commands=['admin'])
async def admin_command(message: types.Message):
    """Handle /admin command"""
    try:
        if message.from_user.id == ADMIN_ID:
            await admin_handlers.show_admin_panel(message)
            logger.info(f"Admin {message.from_user.id} accessed admin panel")
        else:
            await message.answer("❌ شما دسترسی ادمین ندارید!")
            logger.warning(f"Unauthorized admin access attempt by {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in admin command: {e}")

@dp.message_handler(commands=['stats'])
async def stats_command(message: types.Message):
    """Handle /stats command"""
    try:
        if message.from_user.id == ADMIN_ID:
            await admin_handlers.send_quick_stats(message)
            logger.info(f"Admin {message.from_user.id} requested stats")
        else:
            await message.answer("❌ شما دسترسی به این دستور ندارید!")
    except Exception as e:
        logger.error(f"Error in stats command: {e}")

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    """Handle /help command"""
    try:
        help_text = """
🤖 راهنمای ربات

📋 دستورات موجود:
• /start - شروع کار با ربات
• /help - نمایش این راهنما

🎯 قابلیت‌های ربات:
• 🔗 سیستم دعوت دوستان
• 🎁 دریافت جوایز و امتیاز
• 📊 مشاهده آمار شخصی
• 🏆 شرکت در رنکینگ

💡 برای استفاده از ربات، ابتدا در کانال عضو شوید.
        """
        await message.answer(help_text)
        logger.info(f"User {message.from_user.id} requested help")
    except Exception as e:
        logger.error(f"Error in help command: {e}")

@dp.message_handler(commands=['backup'])
async def backup_command(message: types.Message):
    """Handle /backup command (admin only)"""
    try:
        if message.from_user.id == ADMIN_ID:
            await admin_handlers.create_backup(message)
            logger.info(f"Admin {message.from_user.id} created backup")
        else:
            await message.answer("❌ شما دسترسی به این دستور ندارید!")
    except Exception as e:
        logger.error(f"Error in backup command: {e}")

# ==================== MESSAGE HANDLERS ====================

@dp.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'animation'])
async def handle_messages(message: types.Message):
    """Handle all types of messages"""
    try:
        # Update user activity
        await db.update_user_activity(message.from_user.id)
        
        # Handle admin messages (like broadcast creation)
        if message.from_user.id == ADMIN_ID:
            await admin_handlers.handle_admin_message(message)
        else:
            # Handle regular user messages
            if message.text and not message.text.startswith('/'):
                # Log user message for analytics
                await db.log_analytics('message_sent', message.from_user.id, {
                    'message_type': 'text',
                    'message_length': len(message.text)
                })
                
                # Auto-response for common questions
                await handle_auto_responses(message)
    
    except Exception as e:
        logger.error(f"Error handling message from {message.from_user.id}: {e}")

async def handle_auto_responses(message: types.Message):
    """Handle automatic responses to common questions"""
    text = message.text.lower()
    
    auto_responses = {
        'سلام': 'سلام! 👋 از دکمه‌های زیر پیام برای استفاده از ربات استفاده کنید.',
        'راهنما': 'برای راهنمایی از دستور /help استفاده کنید.',
        'پشتیبانی': 'برای پشتیبانی از منوی اصلی گزینه "پشتیبانی" را انتخاب کنید.',
        'امتیاز': 'برای مشاهده امتیاز خود از منوی "آمار من" استفاده کنید.',
        'دعوت': 'برای دعوت دوستان از منوی "دعوت دوستان" استفاده کنید.'
    }
    
    for keyword, response in auto_responses.items():
        if keyword in text:
            await message.answer(response)
            await db.log_analytics('auto_response', message.from_user.id, keyword)
            break

# ==================== CALLBACK QUERY HANDLERS ====================

@dp.callback_query_handler()
async def handle_callback_queries(callback: types.CallbackQuery):
    """Handle all callback queries"""
    try:
        # Update user activity
        await db.update_user_activity(callback.from_user.id)
        
        # Log callback for analytics
        await db.log_analytics('button_click', callback.from_user.id, callback.data)
        
        # Route callback queries to appropriate handlers
        if callback.data.startswith(('admin_', 'broadcast_')):
            await admin_handlers.handle_callback_query(callback)
        elif callback.data.startswith(('referral_', 'my_referrals', 'claim_reward', 'copy_link', 'how_referral')):
            await referral_handlers.handle_callback_query(callback)
        elif callback.data.startswith(('ad_', 'campaign_', 'cross_', 'smart_', 'ab_', 'opt_', 'analytics_')):
            await advertising_handlers.handle_callback_query(callback)
        else:
            await user_handlers.handle_callback_query(callback)
        
        logger.info(f"Callback query handled: {callback.data} from user {callback.from_user.id}")
    
    except Exception as e:
        logger.error(f"Error handling callback query {callback.data} from {callback.from_user.id}: {e}")
        await callback.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)

# ==================== INLINE QUERY HANDLERS ====================

@dp.inline_handler()
async def handle_inline_queries(inline_query: types.InlineQuery):
    """Handle inline queries for sharing referral links"""
    try:
        user_id = inline_query.from_user.id
        query = inline_query.query
        
        # Check if user exists in database
        user_data = await db.get_user(user_id)
        if not user_data:
            return
        
        # Generate referral link
        bot_info = await bot.get_me()
        from utils.helpers import BotHelpers
        helpers = BotHelpers()
        referral_link = helpers.generate_referral_link(user_id, bot_info.username)
        
        # Create inline result
        result = types.InlineQueryResultArticle(
            id='referral_share',
            title='🎁 دعوت به ربات',
            description='دوستان خود را دعوت کنید و جایزه بگیرید!',
            input_message_content=types.InputTextMessageContent(
                message_text=f"""
🎁 سلام! 

به ربات فوق‌العاده‌ای دعوتت می‌کنم که با دعوت دوستان می‌تونی جایزه بگیری!

🔗 لینک عضویت:
{referral_link}

🎯 مزایا:
• دریافت محتوای ویژه
• کسب امتیاز با دعوت دوستان  
• شرکت در قرعه‌کشی‌ها
• دسترسی به جوایز انحصاری

👆 روی لینک کلیک کن و شروع کن!
                """,
                parse_mode='Markdown'
            ),
            thumb_url='https://via.placeholder.com/150x150.png?text=🎁'
        )
        
        await bot.answer_inline_query(
            inline_query.id,
            results=[result],
            cache_time=300,
            is_personal=True
        )
        
        # Log inline query
        await db.log_analytics('inline_query', user_id, query)
        
    except Exception as e:
        logger.error(f"Error handling inline query from {inline_query.from_user.id}: {e}")

# ==================== ERROR HANDLERS ====================

@dp.errors_handler()
async def handle_errors(update: types.Update, exception: Exception):
    """Handle all errors"""
    logger.error(f"Error occurred: {exception}")
    logger.error(f"Update: {update}")
    
    # Try to send error message to admin
    try:
        error_message = f"""
🚨 خطا در ربات

⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
❌ خطا: {str(exception)}
📝 جزئیات: {str(update)}
        """
        await bot.send_message(ADMIN_ID, error_message)
    except:
        pass  # If we can't send to admin, just log it
    
    return True  # Mark error as handled

# ==================== STARTUP AND SHUTDOWN ====================

async def set_bot_commands():
    """Set bot commands for menu"""
    commands = [
        BotCommand(command="start", description="شروع کار با ربات"),
        BotCommand(command="help", description="راهنمای استفاده"),
    ]
    
    # Add admin commands for admin user
    admin_commands = commands + [
        BotCommand(command="admin", description="پنل مدیریت"),
        BotCommand(command="stats", description="آمار سریع"),
        BotCommand(command="backup", description="پشتیبان‌گیری"),
    ]
    
    # Set commands for all users
    await bot.set_my_commands(commands)
    
    # Set admin commands for admin
    await bot.set_my_commands(
        admin_commands,
        scope=types.BotCommandScopeChat(chat_id=ADMIN_ID)
    )

async def on_startup(dp):
    """Initialize bot on startup"""
    logger.info("🚀 Bot is starting up...")
    
    try:
        # Initialize database
        await db.init_db()
        logger.info("✅ Database initialized")
        
        # Set bot commands
        await set_bot_commands()
        logger.info("✅ Bot commands set")
        
        # Start scheduler
        scheduler.start()
        logger.info("✅ Scheduler started")
        
        # Start campaign manager
        campaign_manager.start()
        logger.info("✅ Campaign manager started")
        
        # Get bot info
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot info: @{bot_info.username}")
        
        # Send startup notification to admin
        startup_message = f"""
🚀 ربات با موفقیت راه‌اندازی شد!

🤖 نام ربات: {bot_info.first_name}
👤 نام کاربری: @{bot_info.username}
⏰ زمان شروع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ سیستم‌های فعال:
• پایگاه داده
• سیستم زمان‌بندی
• مدیر کمپین‌ها
• سیستم تحلیل

🎯 ربات آماده دریافت پیام‌ها است!
        """
        
        await bot.send_message(ADMIN_ID, startup_message)
        logger.info("✅ Startup notification sent to admin")
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise

async def on_shutdown(dp):
    """Cleanup on shutdown"""
    logger.info("⏹️ Bot is shutting down...")
    
    try:
        # Stop scheduler
        scheduler.stop()
        logger.info("✅ Scheduler stopped")
        
        # Stop campaign manager
        campaign_manager.stop()
        logger.info("✅ Campaign manager stopped")
        
        # Send shutdown notification to admin
        shutdown_message = f"""
⏹️ ربات متوقف شد

⏰ زمان توقف: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 آمار نهایی در دسترس است.
        """
        
                await bot.send_message(ADMIN_ID, shutdown_message)
        logger.info("✅ Shutdown notification sent to admin")
        
        # Close bot session
        await bot.close()
        logger.info("✅ Bot session closed")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# ==================== PERIODIC TASKS ====================

async def periodic_health_check():
    """Periodic health check"""
    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            # Check database connection
            stats = await db.get_user_stats()
            
            # Check bot connection
            bot_info = await bot.get_me()
            
            # Log health status
            logger.info(f"Health check passed - Users: {stats['total_users']}, Bot: @{bot_info.username}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
            # Try to notify admin about health issues
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"⚠️ مشکل در سلامت ربات:\n{str(e)}"
                )
            except:
                pass

async def periodic_cleanup():
    """Periodic cleanup of old data"""
    while True:
        try:
            await asyncio.sleep(86400)  # Run daily
            
            # Clean old analytics data (older than 90 days)
            async with db.get_connection() as conn:
                await conn.execute("""
                    DELETE FROM analytics 
                    WHERE timestamp < datetime('now', '-90 days')
                """)
                await conn.commit()
            
            logger.info("✅ Periodic cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

# ==================== MAIN EXECUTION ====================

def main():
    """Main function to start the bot"""
    logger.info("🤖 Starting Telegram Channel Bot...")
    
    # Start background tasks
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_health_check())
    loop.create_task(periodic_cleanup())
    
    # Start bot
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        timeout=20,
        relax=0.1
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise