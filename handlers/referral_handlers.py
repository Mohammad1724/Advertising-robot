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

👥 تعداد دعوت‌های شما: {self.helpers.format_number(user_data[6])} نفر
💎 امتیاز کسب شده: {self.helpers.format_number(user_data[7])} امتیاز

🎁 پاداش هر دعوت:
• 10 امتیاز فوری
• دسترسی به محتوای ویژه
• شرکت در قرعه‌کشی‌ها

🔗 لینک دعوت شما:
`{referral_link}`

💡 هر چه بیشتر دعوت کنید، جوایز بهتری دریافت می‌کنید!
        """
        
        await callback.message.edit_text(referral_text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def show_my_referrals(self, callback: types.CallbackQuery):
        """Show user's referral list and statistics"""
        user_id = callback.from_user.id
        
        # Get referral statistics
        async with self.db.get_connection() as db:
            # Get referred users
            async with db.execute("""
                SELECT u.first_name, u.join_date, r.date
                FROM referrals r
                JOIN users u ON r.referred_id = u.user_id
                WHERE r.referrer_id = ?
                ORDER BY r.date DESC
                LIMIT 20
            """, (user_id,)) as cursor:
                referrals = await cursor.fetchall()
            
            # Get referral stats by month
            async with db.execute("""
                SELECT strftime('%Y-%m', date) as month, COUNT(*) as count
                FROM referrals
                WHERE referrer_id = ?
                GROUP BY month
                ORDER BY month DESC
                LIMIT 6
            """, (user_id,)) as cursor:
                monthly_stats = await cursor.fetchall()
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="referral_menu")
        keyboard.add(back_btn)
        
        referrals_text = "👥 لیست دعوت‌های شما\n\n"
        
        if referrals:
            referrals_text += "📋 آخرین دعوت‌ها:\n"
            for i, referral in enumerate(referrals[:10], 1):
                name = referral[0] or "کاربر ناشناس"
                date = self.helpers.format_datetime(referral[2])
                referrals_text += f"{i}. {name} - {date}\n"
            
            if len(referrals) > 10:
                referrals_text += f"\n... و {len(referrals) - 10} نفر دیگر\n"
            
            if monthly_stats:
                referrals_text += "\n📊 آمار ماهانه:\n"
                for month, count in monthly_stats:
                    referrals_text += f"📅 {month}: {count} دعوت\n"
        else:
            referrals_text += "هنوز کسی را دعوت نکرده‌اید!\n"
            referrals_text += "لینک خود را با دوستان به اشتراک بگذارید. 🚀"
        
        await callback.message.edit_text(referrals_text, reply_markup=keyboard)
    
    async def show_referral_rewards(self, callback: types.CallbackQuery):
        """Show available referral rewards"""
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            return
        
        referrals = user_data[6]
        points = user_data[7]
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        # Define reward tiers
        rewards = [
            {"referrals": 5, "points": 50, "title": "🥉 برنزی", "desc": "محتوای ویژه"},
            {"referrals": 10, "points": 100, "title": "🥈 نقره‌ای", "desc": "محتوای VIP"},
            {"referrals": 25, "points": 250, "title": "🥇 طلایی", "desc": "محتوای پریمیوم"},
            {"referrals": 50, "points": 500, "title": "💎 پلاتینی", "desc": "دسترسی کامل"},
            {"referrals": 100, "points": 1000, "title": "👑 الماسی", "desc": "جوایز ویژه"}
        ]
        
        # Add claimable rewards
        for reward in rewards:
            if referrals >= reward["referrals"] and points >= reward["points"]:
                claim_btn = InlineKeyboardButton(
                    f"🎁 دریافت {reward['title']}", 
                    callback_data=f"claim_reward_{reward['referrals']}"
                )
                keyboard.add(claim_btn)
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="referral_menu")
        keyboard.add(back_btn)
        
        rewards_text = f"""
🎁 جوایز سیستم دعوت

💎 امتیاز فعلی: {self.helpers.format_number(points)}
👥 دعوت‌های موفق: {self.helpers.format_number(referrals)}

🏆 سطوح جوایز:

"""
        
        for reward in rewards:
            status = "✅" if referrals >= reward["referrals"] else "🔒"
            progress = f"({referrals}/{reward['referrals']})"
            rewards_text += f"{status} {reward['title']} {progress}\n"
            rewards_text += f"   └ {reward['desc']}\n\n"
        
        rewards_text += "💡 با دعوت بیشتر، به سطوح بالاتر برسید!"
        
        await callback.message.edit_text(rewards_text, reply_markup=keyboard)
    
    async def show_how_referral_works(self, callback: types.CallbackQuery):
        """Show how referral system works"""
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="referral_menu")
        keyboard.add(back_btn)
        
        how_it_works_text = """
❓ چگونه سیستم دعوت کار می‌کند؟

🔗 مرحله ۱: دریافت لینک
لینک اختصاصی خود را از منوی دعوت کپی کنید.

📤 مرحله ۲: اشتراک‌گذاری
لینک را با دوستان، خانواده یا در شبکه‌های اجتماعی به اشتراک بگذارید.

✅ مرحله ۳: عضویت
وقتی کسی از طریق لینک شما عضو شود و در کانال عضو شود، شما پاداش می‌گیرید.

🎁 مرحله ۴: دریافت پاداش
• 10 امتیاز فوری
• دسترسی به محتوای ویژه
• شرکت در قرعه‌کشی‌ها

💡 نکات مهم:
• هر نفر فقط یک بار قابل شمارش است
• کاربر باید در کانال عضو شود
• امتیازات قابل تبدیل به جوایز هستند

🚀 شروع کنید و اولین دعوت خود را ارسال کنید!
        """
        
        await callback.message.edit_text(how_it_works_text, reply_markup=keyboard)
    
    async def handle_copy_link(self, callback: types.CallbackQuery):
        """Handle copy link request"""
        user_id = int(callback.data.split('_')[2])
        
        if callback.from_user.id != user_id:
            await callback.answer("این لینک متعلق به شما نیست!", show_alert=True)
            return
        
        bot_info = await self.bot.get_me()
        referral_link = self.helpers.generate_referral_link(user_id, bot_info.username)
        
        await callback.answer(f"لینک کپی شد:\n{referral_link}", show_alert=True)
    
    async def handle_claim_reward(self, callback: types.CallbackQuery):
        """Handle reward claim"""
        reward_level = int(callback.data.split('_')[2])
        user_id = callback.from_user.id
        user_data = await self.db.get_user(user_id)
        
        if not user_data:
            await callback.answer("خطا در دریافت اطلاعات!", show_alert=True)
            return
        
        # Check if user qualifies for reward
        if user_data[6] >= reward_level:
            # Here you would implement the actual reward giving logic
            # For now, just show a success message
            
            await self.db.log_analytics('reward_claimed', user_id, {'level': reward_level})
            
            await callback.answer(
                f"🎉 تبریک! جایزه سطح {reward_level} با موفقیت دریافت شد!",
                show_alert=True
            )
            
            # Refresh the rewards menu
            await self.show_referral_rewards(callback)
        else:
            await callback.answer(
                f"شما هنوز واجد شرایط این جایزه نیستید!\nتعداد دعوت مورد نیاز: {reward_level}",
                show_alert=True
            )
    
    async def handle_callback_query(self, callback: types.CallbackQuery):
        """Handle referral-related callback queries"""
        if callback.data == "referral_menu":
            await self.show_referral_menu(callback)
        elif callback.data == "my_referrals":
            await self.show_my_referrals(callback)
        elif callback.data == "referral_rewards":
            await self.show_referral_rewards(callback)
        elif callback.data == "how_referral_works":
            await self.show_how_referral_works(callback)
        elif callback.data.startswith("copy_link_"):
            await self.handle_copy_link(callback)
        elif callback.data.startswith("claim_reward_"):
            await self.handle_claim_reward(callback)