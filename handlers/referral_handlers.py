from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import BotHelpers

class ReferralHandlers:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.helpers = BotHelpers()
    
    async def show_referral_menu(self, callback: types.CallbackQuery):
        """Show referral system main menu"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await callback.answer("خطا در دریافت اطلاعات!", show_alert=True)
            return
        
        bot_info = await self.bot.get_me()
        referral_link = self.helpers.generate_referral_link(user_id, bot_info.username)
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Share button with inline query
        share_btn = InlineKeyboardButton(
            "📤 اشتراک‌گذاری", 
            switch_inline_query=f"🎁 به ربات ما بپیوندید و جایزه بگیرید!\n{referral_link}"
        )
        
        # Copy link button
        copy_btn = InlineKeyboardButton("📋 کپی لینک", callback_data=f"copy_link_{user_id}")
        
        # Statistics and rewards
        my_referrals_btn = InlineKeyboardButton("👥 دعوت‌های من", callback_data="my_referrals")
        referral_rewards_btn = InlineKeyboardButton("🎁 جوایز دعوت", callback_data="referral_rewards")
        
        # How it works
        how_it_works_btn = InlineKeyboardButton("❓ چگونه کار می‌کند؟", callback_data="how_referral_works")
        
        # Back button
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")
        
        keyboard.add(share_btn, copy_btn)
        keyboard.add(my_referrals_btn, referral_rewards_btn)
        keyboard.add(how_it_works_btn)
        keyboard.add(back_btn)
        
        referral_text = f"""
🔗 سیستم دعوت دوستان

👥 تعداد دع