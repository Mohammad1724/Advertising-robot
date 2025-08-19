from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import asyncio
from utils.helpers import BotHelpers
from utils.analytics import Analytics

class AdminHandlers:
    def __init__(self, bot, db, admin_id):
        self.bot = bot
        self.db = db
        self.admin_id = admin_id
        self.helpers = BotHelpers()
        self.analytics = Analytics(db)
        self.broadcast_state = {}
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id == self.admin_id
    
    async def show_admin_panel(self, message: types.Message):
        """Show admin panel main menu"""
        if not self.is_admin(message.from_user.id):
            await message.answer("❌ شما دسترسی ادمین ندارید!")
            return
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Statistics
        stats_btn = InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats")
        analytics_btn = InlineKeyboardButton("📈 تحلیل‌ها", callback_data="admin_analytics")
        
        # User management
        users_btn = InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")
        broadcast_btn = InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast")
        
        # Content management
        content_btn = InlineKeyboardButton("🎁 محتوای ویژه", callback_data="admin_content")
        referral_btn = InlineKeyboardButton("🔗 مدیریت ارجاع", callback_data="admin_referral")
        
        # System
        system_btn = InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")
        logs_btn = InlineKeyboardButton("📝 لاگ‌ها", callback_data="admin_logs")
        
        keyboard.add(stats_btn, analytics_btn)
        keyboard.add(users_btn, broadcast_btn)
        keyboard.add(content_btn, referral_btn)
        keyboard.add(system_btn, logs_btn)
        
        admin_text = """
🔐 پنل مدیریت ربات

خوش آمدید! از منوی زیر برای مدیریت ربات استفاده کنید:

📊 آمار و تحلیل‌ها
👥 مدیریت کاربران و پیام‌رسانی
🎁 مدیریت محتوا و جوایز
⚙️ تنظیمات سیستم
        """
        
        await message.answer(admin_text, reply_markup=keyboard)
    
    async def show_admin_stats(self, callback: types.CallbackQuery):
        """Show comprehensive bot statistics"""
        if not self.is_admin(callback.from_user.id):
            return
        
        # Get statistics
        user_stats = await self.db.get_user_stats()
        referral_stats = await self.analytics.get_referral_stats()
        activity_stats = await self.analytics.get_activity_stats()
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        refresh_btn = InlineKeyboardButton("🔄 بروزرسانی", callback_data="admin_stats")
        detailed_btn = InlineKeyboardButton("📈 جزئیات بیشتر", callback_data="admin_analytics")
        export_btn = InlineKeyboardButton("📤 خروجی Excel", callback_data="admin_export")
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
        
        keyboard.add(refresh_btn, detailed_btn)
        keyboard.add(export_btn)
        keyboard.add(back_btn)
        
        stats_text = f"""
📊 آمار کلی ربات

👥 کاربران:
• کل کاربران: {self.helpers.format_number(user_stats['total_users'])}
• اعضای فعال: {self.helpers.format_number(user_stats['active_members'])}
• کاربران امروز: {self.helpers.format_number(user_stats['today_users'])}
• فعال این هفته: {self.helpers.format_number(activity_stats['weekly_active'])}

🔗 سیستم ارجاع:
• کل ارجاعات: {self.helpers.format_number(referral_stats['total_referrals'])}
• میانگین ارجاع: {referral_stats['avg_referrals']}
• برترین کاربر: {referral_stats['top_referrer']['name']} ({referral_stats['top_referrer']['count']})
• ارجاعات این هفته: {self.helpers.format_number(referral_stats['week_referrals'])}

📈 فعالیت:
• فعال ۲۴ ساعت: {self.helpers.format_number(activity_stats['daily_active'])}
• فعال ۷ روز: {self.helpers.format_number(activity_stats['weekly_active'])}
• فعال ۳۰ روز: {self.helpers.format_number(activity_stats['monthly_active'])}

🕐 آخرین بروزرسانی: {datetime.now().strftime('%H:%M:%S')}
        """
        
        await callback.message.edit_text(stats_text, reply_markup=keyboard)
    
    async def show_admin_analytics(self, callback: types.CallbackQuery):
        """Show detailed analytics"""
        if not self.is_admin(callback.from_user.id):
            return
        
        # Get detailed analytics
        popular_actions = await self.analytics.get_popular_actions(5)
        hourly_activity = await self.analytics.get_hourly_activity()
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_stats")
        keyboard.add(back_btn)
        
        # Find peak hour
        peak_hour = max(hourly_activity.items(), key=lambda x: x[1])
        
        analytics_text = f"""
📈 تحلیل‌های تفصیلی

🔥 محبوب‌ترین عملیات (۷ روز اخیر):
"""
        
        for action, count in popular_actions:
            analytics_text += f"• {action}: {self.helpers.format_number(count)}\n"
        
        analytics_text += f"""

⏰ ساعت پیک فعالیت: {peak_hour[0]}:00 ({self.helpers.format_number(peak_hour[1])} فعالیت)

📊 توزیع فعالیت در ساعات مختلف:
"""
        
        # Show hourly distribution (simplified)
        for hour in range(0, 24, 4):
            activity = hourly_activity.get(hour, 0)
            bar = "█" * min(int(activity / 10), 10)
            analytics_text += f"{hour:02d}:00 {bar} {activity}\n"
        
        await callback.message.edit_text(analytics_text, reply_markup=keyboard)
    
    async def show_user_management(self, callback: types.CallbackQuery):
        """Show user management options"""
        if not self.is_admin(callback.from_user.id):
            return
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        search_btn = InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user")
        ban_btn = InlineKeyboardButton("🚫 مسدود کردن", callback_data="admin_ban_user")
        unban_btn = InlineKeyboardButton("✅ رفع مسدودی", callback_data="admin_unban_user")
        top_users_btn = InlineKeyboardButton("🏆 برترین کاربران", callback_data="admin_top_users")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
        
        keyboard.add(search_btn, ban_btn)
        keyboard.add(unban_btn, top_users_btn)
        keyboard.add(back_btn)
        
        user_mgmt_text = """
👥 مدیریت کاربران

از گزینه‌های زیر برای مدیریت کاربران استفاده کنید:

🔍 جستجو و مشاهده اطلاعات کاربر
🚫 مسدود کردن کاربران مشکل‌ساز
✅ رفع مسدودی کاربران
🏆 مشاهده برترین کاربران
        """
        
        await callback.message.edit_text(user_mgmt_text, reply_markup=keyboard)
    
    async def show_broadcast_menu(self, callback: types.CallbackQuery):
        """Show broadcast message options"""
        if not self.is_admin(callback.from_user.id):
            return
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        new_broadcast_btn = InlineKeyboardButton("📝 پیام جدید", callback_data="admin_new_broadcast")
        scheduled_btn = InlineKeyboardButton("⏰ پیام‌های زمان‌بندی شده", callback_data="admin_scheduled")
        history_btn = InlineKeyboardButton("📋 تاریخچه ارسال", callback_data="admin_broadcast_history")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
        
        keyboard.add(new_broadcast_btn)
        keyboard.add(scheduled_btn, history_btn)
        keyboard.add(back_btn)
        
        broadcast_text = """
📢 مدیریت پیام‌های همگانی

📝 ایجاد پیام جدید برای ارسال به همه کاربران
⏰ مدیریت پیام‌های زمان‌بندی شده
📋 مشاهده تاریخچه پیام‌های ارسالی

⚠️ توجه: پیام‌های همگانی با احتیاط ارسال شوند.
        """
        
        await callback.message.edit_text(broadcast_text, reply_markup=keyboard)
    
    async def start_new_broadcast(self, callback: types.CallbackQuery):
        """Start creating new broadcast message"""
        if not self.is_admin(callback.from_user.id):
            return
        
        user_id = callback.from_user.id
        self.broadcast_state[user_id] = {'step': 'waiting_message'}
        
        keyboard = InlineKeyboardMarkup()
        cancel_btn = InlineKeyboardButton("❌ لغو", callback_data="admin_broadcast")
        keyboard.add(cancel_btn)
        
        await callback.message.edit_text(
            "📝 ایجاد پیام همگانی\n\n"
            "لطفاً متن پیام خود را ارسال کنید:\n"
            "• می‌توانید متن، عکس، ویدیو یا فایل ارسال کنید\n"
            "• از فرمت‌بندی Markdown استفاده کنید\n"
            "• برای لغو از دکمه زیر استفاده کنید",
            reply_markup=keyboard
        )
    
    async def handle_broadcast_message(self, message: types.Message):
        """Handle broadcast message from admin"""
        user_id = message.from_user.id
        
        if not self.is_admin(user_id) or user_id not in self.broadcast_state:
            return
        
        if self.broadcast_state[user_id]['step'] != 'waiting_message':
            return
        
        # Store message details
        self.broadcast_state[user_id].update({
            'step': 'confirm',
            'message_text': message.text or message.caption,
            'message_type': 'text' if message.text else self.helpers.get_file_type(message),
            'file_id': self._get_file_id(message)
        })
        
        # Show confirmation
        keyboard = InlineKeyboardMarkup(row_width=2)
        send_now_btn = InlineKeyboardButton("📤 ارسال فوری", callback_data="admin_send_broadcast")
        schedule_btn = InlineKeyboardButton("⏰ زمان‌بندی", callback_data="admin_schedule_broadcast")
        preview_btn = InlineKeyboardButton("👁 پیش‌نمایش", callback_data="admin_preview_broadcast")
        cancel_btn = InlineKeyboardButton("❌ لغو", callback_data="admin_broadcast")
        
        keyboard.add(send_now_btn, schedule_btn)
        keyboard.add(preview_btn)
        keyboard.add(cancel_btn)
        
        await message.answer(
            "✅ پیام دریافت شد!\n\n"
            "گزینه مورد نظر را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    async def send_broadcast(self, callback: types.CallbackQuery):
        """Send broadcast message to all users"""
        if not self.is_admin(callback.from_user.id):
            return
        
        user_id = callback.from_user.id
        if user_id not in self.broadcast_state:
            await callback.answer("خطا در ارسال پیام!", show_alert=True)
            return
        
        broadcast_data = self.broadcast_state[user_id]
        
        # Get all users
        users = await self.db.get_all_users()
        total_users = len(users)
        
        # Update message to show progress
        await callback.message.edit_text(
            f"📤 در حال ارسال پیام به {self.helpers.format_number(total_users)} کاربر...\n\n"
            "⏳ لطفاً صبر کنید..."
        )
        
        # Send messages
        sent_count = 0
        failed_count = 0
        
        for user_data in users:
            try:
                user_id_target = user_data[0]
                
                if broadcast_data['message_type'] == 'text':
                    await self.bot.send_message(
                        user_id_target,
                        broadcast_data['message_text'],
                        parse_mode='Markdown'
                    )
                else:
                    # Handle media messages
                    await self._send_media_message(
                        user_id_target,
                        broadcast_data
                    )
                
                sent_count += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.05)
                
            except Exception as e:
                failed_count += 1
                continue
                # Clean up state
        del self.broadcast_state[user_id]
        
        # Show results
        result_text = f"""
✅ ارسال پیام همگانی تکمیل شد!

📊 نتایج:
• کل کاربران: {self.helpers.format_number(total_users)}
• ارسال موفق: {self.helpers.format_number(sent_count)}
• ارسال ناموفق: {self.helpers.format_number(failed_count)}
• نرخ موفقیت: {round((sent_count/total_users)*100, 1)}%

⏰ زمان ارسال: {datetime.now().strftime('%Y/%m/%d - %H:%M')}
        """
        
        keyboard = InlineKeyboardMarkup()
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_broadcast")
        keyboard.add(back_btn)
        
        await callback.message.edit_text(result_text, reply_markup=keyboard)
        
        # Log the broadcast
        await self.db.log_analytics('broadcast_sent', callback.from_user.id, {
            'total_users': total_users,
            'sent_count': sent_count,
            'failed_count': failed_count
        })
    
    def _get_file_id(self, message):
        """Extract file ID from message"""
        if message.photo:
            return message.photo[-1].file_id
        elif message.video:
            return message.video.file_id
        elif message.document:
            return message.document.file_id
        elif message.audio:
            return message.audio.file_id
        elif message.voice:
            return message.voice.file_id
        elif message.animation:
            return message.animation.file_id
        return None
    
    async def _send_media_message(self, user_id, broadcast_data):
        """Send media message to user"""
        file_id = broadcast_data['file_id']
        caption = broadcast_data['message_text']
        message_type = broadcast_data['message_type']
        
        if message_type == 'photo':
            await self.bot.send_photo(user_id, file_id, caption=caption, parse_mode='Markdown')
        elif message_type == 'video':
            await self.bot.send_video(user_id, file_id, caption=caption, parse_mode='Markdown')
        elif message_type == 'document':
            await self.bot.send_document(user_id, file_id, caption=caption, parse_mode='Markdown')
        elif message_type == 'audio':
            await self.bot.send_audio(user_id, file_id, caption=caption, parse_mode='Markdown')
        elif message_type == 'voice':
            await self.bot.send_voice(user_id, file_id, caption=caption, parse_mode='Markdown')
        elif message_type == 'animation':
            await self.bot.send_animation(user_id, file_id, caption=caption, parse_mode='Markdown')
    
    async def show_content_management(self, callback: types.CallbackQuery):
        """Show exclusive content management"""
        if not self.is_admin(callback.from_user.id):
            return
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        add_content_btn = InlineKeyboardButton("➕ افزودن محتوا", callback_data="admin_add_content")
        list_content_btn = InlineKeyboardButton("📋 لیست محتوا", callback_data="admin_list_content")
        edit_content_btn = InlineKeyboardButton("✏️ ویرایش", callback_data="admin_edit_content")
        delete_content_btn = InlineKeyboardButton("🗑 حذف", callback_data="admin_delete_content")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
        
        keyboard.add(add_content_btn, list_content_btn)
        keyboard.add(edit_content_btn, delete_content_btn)
        keyboard.add(back_btn)
        
        content_text = """
🎁 مدیریت محتوای ویژه

➕ افزودن محتوای جدید
📋 مشاهده لیست محتواها
✏️ ویرایش محتوای موجود
🗑 حذف محتوای غیرضروری

💡 محتوای ویژه بر اساس تعداد دعوت‌ها و امتیازات قابل دسترسی است.
        """
        
        await callback.message.edit_text(content_text, reply_markup=keyboard)
    
    async def handle_callback_query(self, callback: types.CallbackQuery):
        """Handle admin callback queries"""
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ دسترسی غیرمجاز!", show_alert=True)
            return
        
        if callback.data == "admin_panel":
            await self.show_admin_panel(callback.message)
        elif callback.data == "admin_stats":
            await self.show_admin_stats(callback)
        elif callback.data == "admin_analytics":
            await self.show_admin_analytics(callback)
        elif callback.data == "admin_users":
            await self.show_user_management(callback)
        elif callback.data == "admin_broadcast":
            await self.show_broadcast_menu(callback)
        elif callback.data == "admin_new_broadcast":
            await self.start_new_broadcast(callback)
        elif callback.data == "admin_send_broadcast":
            await self.send_broadcast(callback)
        elif callback.data == "admin_content":
            await self.show_content_management(callback)
        
        await callback.answer()
    
    async def handle_admin_message(self, message: types.Message):
        """Handle messages from admin"""
        if not self.is_admin(message.from_user.id):
            return
        
        user_id = message.from_user.id
        
        # Handle broadcast message creation
        if user_id in self.broadcast_state:
            await self.handle_broadcast_message(message)
            return
        
        # Handle admin commands
        if message.text and message.text.startswith('/'):
            await self.handle_admin_commands(message)
    
    async def handle_admin_commands(self, message: types.Message):
        """Handle admin commands"""
        command = message.text.lower()
        
        if command == '/admin':
            await self.show_admin_panel(message)
        elif command == '/stats':
            await self.send_quick_stats(message)
        elif command == '/backup':
            await self.create_backup(message)
        elif command.startswith('/ban '):
            user_id = command.split()[1]
            await self.ban_user(message, user_id)
        elif command.startswith('/unban '):
            user_id = command.split()[1]
            await self.unban_user(message, user_id)
    
    async def send_quick_stats(self, message: types.Message):
        """Send quick statistics"""
        stats = await self.db.get_user_stats()
        
        quick_stats = f"""
📊 آمار سریع:

👥 کل کاربران: {self.helpers.format_number(stats['total_users'])}
✅ اعضای فعال: {self.helpers.format_number(stats['active_members'])}
🆕 کاربران امروز: {self.helpers.format_number(stats['today_users'])}
🔗 کل ارجاعات: {self.helpers.format_number(stats['total_referrals'])}

⏰ {datetime.now().strftime('%Y/%m/%d - %H:%M')}
        """
        
        await message.answer(quick_stats)
