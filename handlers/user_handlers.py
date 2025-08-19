گfrom aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import BotHelpers
from config import CHANNEL_ID

class UserHandlers:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.helpers = BotHelpers()
    
    async def start_command(self, message: types.Message):
        """Handle /start command"""
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        
        # Check for referral code
        referrer_id = None
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            referrer_id = self.helpers.decode_referral_id(ref_code)
        
        # Add user to database
        await self.db.add_user(user_id, username, first_name, last_name, referrer_id)
        await self.db.update_user_activity(user_id)
        
        # Log analytics
        await self.db.log_analytics('start_command', user_id, {'referrer_id': referrer_id})
        
        # Add referral if exists
        if referrer_id and referrer_id != user_id:
            success = await self.db.add_referral(referrer_id, user_id)
            if success:
                # Notify referrer
                try:
                    await self.bot.send_message(
                        referrer_id,
                        f"🎉 تبریک! کاربر جدیدی از طریق لینک شما عضو شد!\n"
                        f"👤 {first_name}\n"
                        f"💎 +10 امتیاز دریافت کردید!"
                    )
                except:
                    pass
        
        # Show welcome message
        await self.show_welcome_message(message)
    
    async def show_welcome_message(self, message: types.Message):
        """Show welcome message with membership check"""
        user_name = message.from_user.first_name
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        channel_btn = InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")
        check_btn = InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership")
        keyboard.add(channel_btn, check_btn)
        
        welcome_text = f"""
🌟 سلام {user_name} عزیز! 

به ربات تبلیغاتی کانال ما خوش آمدید!

🎯 امکانات ربات:
• 🔗 سیستم دعوت دوستان
• 🎁 محتوای انحصاری
• 🏆 جدول امتیازات
• 📊 آمار شخصی

💡 برای استفاده از ربات، ابتدا در کانال ما عضو شوید:
        """
        
        await message.answer(welcome_text, reply_markup=keyboard)
    
    async def check_membership(self, callback: types.CallbackQuery):
        """Check user membership in channel"""
        user_id = callback.from_user.id
        
        try:
            member = await self.bot.get_chat_member(CHANNEL_ID, user_id)
            if member.status in ['member', 'administrator', 'creator']:
                # Update membership status
                await self.db.update_membership(user_id, True)
                await self.db.log_analytics('membership_confirmed', user_id)
                
                # Show main menu
                await self.show_main_menu(callback)
            else:
                await callback.answer("❌ شما هنوز در کانال عضو نیستید!", show_alert=True)
        except Exception as e:
            print(f"Error checking membership: {e}")
            await callback.answer("❌ خطا در بررسی عضویت!", show_alert=True)
    
    async def show_main_menu(self, callback: types.CallbackQuery):
        """Show main menu to verified users"""
        user_data = await self.db.get_user(callback.from_user.id)
        level, level_emoji = self.helpers.calculate_user_level(user_data[7])
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Main buttons
        referral_btn = InlineKeyboardButton("🔗 دعوت دوستان", callback_data="referral_menu")
        rewards_btn = InlineKeyboardButton("🎁 جوایز", callback_data="rewards_menu")
        stats_btn = InlineKeyboardButton("📊 آمار من", callback_data="my_stats")
        leaderboard_btn = InlineKeyboardButton("🏆 رنکینگ", callback_data="leaderboard")
        
        # Secondary buttons
        channel_btn = InlineKeyboardButton("📢 کانال ما", url=f"https://t.me/{CHANNEL_ID[1:]}")
        support_btn = InlineKeyboardButton("🆘 پشتیبانی", callback_data="support")
        
        keyboard.add(referral_btn, rewards_btn)
        keyboard.add(stats_btn, leaderboard_btn)
        keyboard.add(channel_btn, support_btn)
        
        main_text = f"""
✅ عضویت شما تایید شد!

👤 {callback.from_user.first_name}
{level_emoji} سطح: {level}
💎 امتیاز: {self.helpers.format_number(user_data[7])}
👥 دعوت‌ها: {self.helpers.format_number(user_data[6])}

🎯 از منوی زیر استفاده کنید:
        """
        
        await callback.message.edit_text(main_text, reply_markup=keyboard)
    
    async def show_my_stats(self, callback: types.CallbackQuery):
        """Show user personal statistics"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await callback.answer("خطا در دریافت اطلاعات!", show_alert=True)
            return
        
        level, level_emoji = self.helpers.calculate_user_level(user_data[7])
        join_date = self.helpers.format_datetime(user_data[5])
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
        keyboard.add(back_btn)
        
        stats_text = f"""
📊 آمار شخصی شما

👤 نام: {user_data[2]}
🆔 شناسه: {user_data[0]}
📅 عضو از: {join_date}

{level_emoji} سطح فعلی: {level}
💎 کل امتیازات: {self.helpers.format_number(user_data[7])}
👥 کل دعوت‌ها: {self.helpers.format_number(user_data[6])}

📈 پیشرفت تا سطح بعد:
{self._get_progress_bar(user_data[7])}

🎯 برای کسب امتیاز بیشتر، دوستان خود را دعوت کنید!
        """
        
        await callback.message.edit_text(stats_text, reply_markup=keyboard)
    
    async def show_leaderboard(self, callback: types.CallbackQuery):
        """Show top users leaderboard"""
        top_users = await self.db.get_top_referrers(10)
        user_id = callback.from_user.id
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
        keyboard.add(back_btn)
        
        leaderboard_text = "🏆 جدول برترین کاربران\n\n"
        
        if top_users:
            for i, user in enumerate(top_users, 1):
                rank_emoji = self.helpers.get_user_rank_emoji(i)
                name = user[1] or "کاربر ناشناس"
                
                # Highlight current user
                if user[0] == user_id:
                    leaderboard_text += f"➤ {rank_emoji} {name} - {self.helpers.format_number(user[2])} دعوت\n"
                else:
                    leaderboard_text += f"{rank_emoji} {name} - {self.helpers.format_number(user[2])} دعوت\n"
            
            # Show current user rank if not in top 10
            user_data = await self.db.get_user(user_id)
            if user_data and user_data[6] > 0:
                user_in_top = any(user[0] == user_id for user in top_users)
                if not user_in_top:
                    leaderboard_text += f"\n📍 رتبه شما: {user_data[6]} دعوت"
        else:
            leaderboard_text += "هنوز کسی دعوت نکرده است!\nاولین نفر باشید! 🚀"
        
        await callback.message.edit_text(leaderboard_text, reply_markup=keyboard)
    
    async def show_support(self, callback: types.CallbackQuery):
        """Show support information"""
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
        keyboard.add(back_btn)
        
        support_text = """
🆘 پشتیبانی و راهنمایی

📞 راه‌های ارتباط:
• 📧 ایمیل: support@example.com
• 💬 تلگرام: @support_username
• 🌐 وبسایت: www.example.com

⏰ ساعات پاسخگویی:
شنبه تا پنج‌شنبه: ۹ صبح تا ۱۸ عصر

❓ سوالات متداول:
• چگونه امتیاز کسب کنم؟
• چگونه دوستان را دعوت کنم؟
• چگونه جوایز را دریافت کنم؟

💡 برای پاسخ سریع، ابتدا راهنمای ربات را مطالعه کنید.
        """
        
        await callback.message.edit_text(support_text, reply_markup=keyboard)
    
    def _get_progress_bar(self, points):
        """Generate progress bar for user level"""
        levels = [0, 50, 100, 200, 500, 1000]
        current_level = 0
        
        for i, level_points in enumerate(levels):
            if points >= level_points:
                current_level = i
        
        if current_level >= len(levels) - 1:
            return "🌟 حداکثر سطح! 🌟"
        
        next_level_points = levels[current_level + 1]
        progress = points - levels[current_level]
        needed = next_level_points - levels[current_level]
        
        filled = int((progress / needed) * 10)
        bar = "🟩" * filled + "⬜" * (10 - filled)
        
        return f"{bar}\n{progress}/{needed} امتیاز تا سطح بعد"
    
    async def handle_callback_query(self, callback: types.CallbackQuery):
        """Handle all callback queries"""
        await self.db.update_user_activity(callback.from_user.id)
        
        if callback.data == "check_membership":
            await self.check_membership(callback)
        elif callback.data == "main_menu":
            await self.show_main_menu(callback)
        elif callback.data == "my_stats":
            await self.show_my_stats(callback)
        elif callback.data == "leaderboard":
            await self.show_leaderboard(callback)
        elif callback.data == "support":
            await self.show_support(callback)
        
        await callback.answer()