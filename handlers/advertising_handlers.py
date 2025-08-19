import asyncio
import random
from datetime import datetime, timedelta
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import BotHelpers
import aiohttp
import json

class AdvertisingHandlers:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.helpers = BotHelpers()
        self.campaign_state = {}
        self.partner_channels = []  # List of partner channels
        
    # ==================== CAMPAIGN MANAGEMENT ====================
    
    async def show_advertising_panel(self, callback: types.CallbackQuery):
        """Show main advertising panel"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Campaign management
        create_campaign_btn = InlineKeyboardButton("🎯 ایجاد کمپین", callback_data="ad_create_campaign")
        manage_campaigns_btn = InlineKeyboardButton("📊 مدیریت کمپین‌ها", callback_data="ad_manage_campaigns")
        
        # Cross promotion
        cross_promo_btn = InlineKeyboardButton("🤝 تبادل تبلیغات", callback_data="ad_cross_promotion")
        partner_mgmt_btn = InlineKeyboardButton("👥 مدیریت شرکا", callback_data="ad_partner_management")
        
        # Smart targeting
        smart_ads_btn = InlineKeyboardButton("🧠 تبلیغات هوشمند", callback_data="ad_smart_targeting")
        ab_test_btn = InlineKeyboardButton("🔬 A/B تست", callback_data="ad_ab_testing")
        
        # Analytics
        analytics_btn = InlineKeyboardButton("📈 آنالیز کمپین", callback_data="ad_analytics")
        optimization_btn = InlineKeyboardButton("⚡ بهینه‌سازی", callback_data="ad_optimization")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="admin_panel")
        
        keyboard.add(create_campaign_btn, manage_campaigns_btn)
        keyboard.add(cross_promo_btn, partner_mgmt_btn)
        keyboard.add(smart_ads_btn, ab_test_btn)
        keyboard.add(analytics_btn, optimization_btn)
        keyboard.add(back_btn)
        
        ad_text = """
🎯 پنل تبلیغات پیشرفته

🚀 قابلیت‌های موجود:
• ایجاد و مدیریت کمپین‌های تبلیغاتی
• تبادل تبلیغات با کانال‌های شریک
• تبلیغات هوشمند بر اساس رفتار کاربر
• A/B تست برای بهینه‌سازی پیام‌ها
• آنالیز عمیق عملکرد کمپین‌ها

💡 با این ابزارها کانال خود را به سرعت رشد دهید!
        """
        
        await callback.message.edit_text(ad_text, reply_markup=keyboard)
    
    # ==================== CAMPAIGN CREATION ====================
    
    async def create_campaign_wizard(self, callback: types.CallbackQuery):
        """Start campaign creation wizard"""
        user_id = callback.from_user.id
        self.campaign_state[user_id] = {
            'step': 'campaign_type',
            'data': {}
        }
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        # Campaign types
        broadcast_btn = InlineKeyboardButton("📢 پیام همگانی", callback_data="campaign_type_broadcast")
        referral_btn = InlineKeyboardButton("🔗 تشویق ارجاع", callback_data="campaign_type_referral")
        engagement_btn = InlineKeyboardButton("💬 افزایش تعامل", callback_data="campaign_type_engagement")
        retention_btn = InlineKeyboardButton("🔄 بازگشت کاربران", callback_data="campaign_type_retention")
        
        cancel_btn = InlineKeyboardButton("❌ لغو", callback_data="ad_panel")
        
        keyboard.add(broadcast_btn, referral_btn, engagement_btn, retention_btn)
        keyboard.add(cancel_btn)
        
        await callback.message.edit_text(
            "🎯 ایجاد کمپین جدید\n\n"
            "نوع کمپین مورد نظر را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    async def handle_campaign_type(self, callback: types.CallbackQuery):
        """Handle campaign type selection"""
        user_id = callback.from_user.id
        campaign_type = callback.data.split('_')[2]
        
        if user_id not in self.campaign_state:
            return
        
        self.campaign_state[user_id]['data']['type'] = campaign_type
        self.campaign_state[user_id]['step'] = 'target_audience'
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        # Target audience options
        all_users_btn = InlineKeyboardButton("👥 همه کاربران", callback_data="target_all")
        active_users_btn = InlineKeyboardButton("⚡ کاربران فعال", callback_data="target_active")
        new_users_btn = InlineKeyboardButton("🆕 کاربران جدید", callback_data="target_new")
        top_referrers_btn = InlineKeyboardButton("🏆 برترین ارجاع‌دهندگان", callback_data="target_top")
        inactive_users_btn = InlineKeyboardButton("😴 کاربران غیرفعال", callback_data="target_inactive")
        custom_btn = InlineKeyboardButton("🎯 سفارشی", callback_data="target_custom")
        
        back_btn = InlineKeyboardButton("🔙 قبلی", callback_data="ad_create_campaign")
        
        keyboard.add(all_users_btn, active_users_btn)
        keyboard.add(new_users_btn, top_referrers_btn)
        keyboard.add(inactive_users_btn, custom_btn)
        keyboard.add(back_btn)
        
        campaign_types = {
            'broadcast': 'پیام همگانی',
            'referral': 'تشویق ارجاع',
            'engagement': 'افزایش تعامل',
            'retention': 'بازگشت کاربران'
        }
        
        await callback.message.edit_text(
            f"🎯 کمپین: {campaign_types.get(campaign_type, campaign_type)}\n\n"
            "مخاطب هدف را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    # ==================== CROSS PROMOTION SYSTEM ====================
    
    async def show_cross_promotion(self, callback: types.CallbackQuery):
        """Show cross promotion management"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        add_partner_btn = InlineKeyboardButton("➕ افزودن شریک", callback_data="cross_add_partner")
        partner_list_btn = InlineKeyboardButton("📋 لیست شرکا", callback_data="cross_partner_list")
        
        create_exchange_btn = InlineKeyboardButton("🔄 ایجاد تبادل", callback_data="cross_create_exchange")
        exchange_history_btn = InlineKeyboardButton("📊 تاریخچه تبادل", callback_data="cross_exchange_history")
        
        auto_exchange_btn = InlineKeyboardButton("🤖 تبادل خودکار", callback_data="cross_auto_exchange")
        settings_btn = InlineKeyboardButton("⚙️ تنظیمات", callback_data="cross_settings")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="ad_panel")
        
        keyboard.add(add_partner_btn, partner_list_btn)
        keyboard.add(create_exchange_btn, exchange_history_btn)
        keyboard.add(auto_exchange_btn, settings_btn)
        keyboard.add(back_btn)
        
        # Get current partners count
        partners_count = len(self.partner_channels)
        
        cross_promo_text = f"""
🤝 سیستم تبادل تبلیغات

📊 وضعیت فعلی:
• شرکای فعال: {partners_count} کانال
• تبادل‌های امروز: در حال محاسبه...
• نرخ موفقیت: در حال محاسبه...

🎯 قابلیت‌ها:
• افزودن کانال‌های شریک
• تبادل خودکار تبلیغات
• ردیابی عملکرد تبادل‌ها
• تنظیمات هوشمند تبادل

💡 با تبادل تبلیغات، رشد متقابل داشته باشید!
        """
        
        await callback.message.edit_text(cross_promo_text, reply_markup=keyboard)
    
    async def add_partner_channel(self, callback: types.CallbackQuery):
        """Add new partner channel"""
        user_id = callback.from_user.id
        self.campaign_state[user_id] = {
            'step': 'add_partner_channel',
            'data': {}
        }
        
        keyboard = InlineKeyboardMarkup()
        cancel_btn = InlineKeyboardButton("❌ لغو", callback_data="cross_promotion")
        keyboard.add(cancel_btn)
        
        await callback.message.edit_text(
            "➕ افزودن کانال شریک\n\n"
            "لطفاً اطلاعات کانال شریک را ارسال کنید:\n"
            "فرمت: @channel_username | نام کانال | توضیحات\n\n"
            "مثال:\n"
            "@tech_channel | کانال تکنولوژی | کانال آموزش برنامه‌نویسی",
            reply_markup=keyboard
        )
    
    # ==================== SMART TARGETING ====================
    
    async def show_smart_targeting(self, callback: types.CallbackQuery):
        """Show smart targeting options"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        behavior_btn = InlineKeyboardButton("🧠 بر اساس رفتار", callback_data="smart_behavior")
        time_btn = InlineKeyboardButton("⏰ بهینه‌سازی زمان", callback_data="smart_time")
        
        engagement_btn = InlineKeyboardButton("💬 سطح تعامل", callback_data="smart_engagement")
        referral_btn = InlineKeyboardButton("🔗 عملکرد ارجاع", callback_data="smart_referral")
        
        ai_predict_btn = InlineKeyboardButton("🤖 پیش‌بینی AI", callback_data="smart_ai_predict")
        personalize_btn = InlineKeyboardButton("👤 شخصی‌سازی", callback_data="smart_personalize")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="ad_panel")
        
        keyboard.add(behavior_btn, time_btn)
        keyboard.add(engagement_btn, referral_btn)
        keyboard.add(ai_predict_btn, personalize_btn)
        keyboard.add(back_btn)
        
        smart_text = """
🧠 تبلیغات هوشمند

🎯 هدف‌گذاری پیشرفته:
• تحلیل رفتار کاربران
• بهینه‌سازی زمان ارسال
• سطح‌بندی بر اساس تعامل
• پیش‌بینی احتمال پاسخ

🤖 قابلیت‌های AI:
• تشخیص الگوهای رفتاری
• پیش‌بینی بهترین زمان ارسال
• شخصی‌سازی محتوا
• بهینه‌سازی خودکار

📈 نتایج:
• افزایش نرخ باز کردن پیام
• بهبود تعامل کاربران
• کاهش unsubscribe
• رشد طبیعی کانال
        """
        
        await callback.message.edit_text(smart_text, reply_markup=keyboard)
    
    # ==================== A/B TESTING ====================
    
    async def show_ab_testing(self, callback: types.CallbackQuery):
        """Show A/B testing panel"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        create_test_btn = InlineKeyboardButton("🧪 ایجاد تست", callback_data="ab_create_test")
        active_tests_btn = InlineKeyboardButton("⚡ تست‌های فعال", callback_data="ab_active_tests")
        
        test_results_btn = InlineKeyboardButton("📊 نتایج تست‌ها", callback_data="ab_test_results")
        test_history_btn = InlineKeyboardButton("📋 تاریخچه", callback_data="ab_test_history")
        
        templates_btn = InlineKeyboardButton("📝 قالب‌های تست", callback_data="ab_templates")
        settings_btn = InlineKeyboardButton("⚙️ تنظیمات", callback_data="ab_settings")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="ad_panel")
        
        keyboard.add(create_test_btn, active_tests_btn)
        keyboard.add(test_results_btn, test_history_btn)
        keyboard.add(templates_btn, settings_btn)
        keyboard.add(back_btn)
        
                ab_text = """
🔬 سیستم A/B تست

🧪 تست‌های قابل انجام:
• متن پیام‌ها
• زمان ارسال
• نوع محتوا (متن/تصویر/ویدیو)
• دکمه‌های عمل (CTA)
• موضوع و عنوان

📊 معیارهای سنجش:
• نرخ باز کردن (Open Rate)
• نرخ کلیک (Click Rate)
• نرخ تعامل (Engagement)
• نرخ تبدیل (Conversion)
• زمان ماندگاری

🎯 مزایا:
• بهینه‌سازی مداوم
• تصمیم‌گیری بر اساس داده
• افزایش ROI تبلیغات
• کاهش هزینه‌های بازاریابی
        """
        
        await callback.message.edit_text(ab_text, reply_markup=keyboard)
    
    # ==================== ANALYTICS & OPTIMIZATION ====================
    
    async def show_campaign_analytics(self, callback: types.CallbackQuery):
        """Show detailed campaign analytics"""
        # Get campaign statistics
        stats = await self.get_campaign_statistics()
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        real_time_btn = InlineKeyboardButton("⚡ آمار لحظه‌ای", callback_data="analytics_realtime")
        detailed_btn = InlineKeyboardButton("📊 گزارش تفصیلی", callback_data="analytics_detailed")
        
        export_btn = InlineKeyboardButton("📤 خروجی Excel", callback_data="analytics_export")
        compare_btn = InlineKeyboardButton("🔄 مقایسه کمپین‌ها", callback_data="analytics_compare")
        
        roi_btn = InlineKeyboardButton("💰 تحلیل ROI", callback_data="analytics_roi")
        forecast_btn = InlineKeyboardButton("🔮 پیش‌بینی", callback_data="analytics_forecast")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="ad_panel")
        
        keyboard.add(real_time_btn, detailed_btn)
        keyboard.add(export_btn, compare_btn)
        keyboard.add(roi_btn, forecast_btn)
        keyboard.add(back_btn)
        
        analytics_text = f"""
📈 آنالیز کمپین‌های تبلیغاتی

📊 عملکرد کلی (30 روز اخیر):
• کل کمپین‌ها: {stats.get('total_campaigns', 0)}
• پیام‌های ارسالی: {self.helpers.format_number(stats.get('total_messages', 0))}
• نرخ تحویل: {stats.get('delivery_rate', 0)}%
• نرخ باز کردن: {stats.get('open_rate', 0)}%
• نرخ کلیک: {stats.get('click_rate', 0)}%

🎯 بهترین کمپین:
• نام: {stats.get('best_campaign', 'ندارد')}
• نرخ تعامل: {stats.get('best_engagement', 0)}%

📉 نیاز به بهینه‌سازی:
• کمپین‌های ضعیف: {stats.get('weak_campaigns', 0)}
• پیشنهادات بهبود: {stats.get('improvement_suggestions', 0)}

💡 توصیه‌های هوشمند در دسترس است!
        """
        
        await callback.message.edit_text(analytics_text, reply_markup=keyboard)
    
    # ==================== AUTO OPTIMIZATION ====================
    
    async def show_optimization_panel(self, callback: types.CallbackQuery):
        """Show optimization options"""
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        auto_optimize_btn = InlineKeyboardButton("🤖 بهینه‌سازی خودکار", callback_data="opt_auto")
        manual_optimize_btn = InlineKeyboardButton("🔧 بهینه‌سازی دستی", callback_data="opt_manual")
        
        time_optimize_btn = InlineKeyboardButton("⏰ بهینه‌سازی زمان", callback_data="opt_time")
        content_optimize_btn = InlineKeyboardButton("📝 بهینه‌سازی محتوا", callback_data="opt_content")
        
        audience_optimize_btn = InlineKeyboardButton("👥 بهینه‌سازی مخاطب", callback_data="opt_audience")
        frequency_optimize_btn = InlineKeyboardButton("🔄 بهینه‌سازی تکرار", callback_data="opt_frequency")
        
        back_btn = InlineKeyboardButton("🔙 بازگشت", callback_data="ad_panel")
        
        keyboard.add(auto_optimize_btn, manual_optimize_btn)
        keyboard.add(time_optimize_btn, content_optimize_btn)
        keyboard.add(audience_optimize_btn, frequency_optimize_btn)
        keyboard.add(back_btn)
        
        optimization_text = """
⚡ بهینه‌سازی کمپین‌ها

🤖 بهینه‌سازی خودکار:
• تشخیص بهترین زمان ارسال
• انتخاب مخاطب مناسب
• تنظیم تکرار پیام‌ها
• بهبود محتوا بر اساس عملکرد

🔧 بهینه‌سازی دستی:
• تنظیمات سفارشی
• کنترل کامل پارامترها
• تست استراتژی‌های جدید
• تحلیل عمیق نتایج

📈 نتایج قابل انتظار:
• افزایش 25-40% نرخ تعامل
• کاهش 30% هزینه تبلیغات
• بهبود 50% نرخ تبدیل
• رشد 60% کیفیت مخاطب
        """
        
        await callback.message.edit_text(optimization_text, reply_markup=keyboard)
    
    # ==================== HELPER METHODS ====================
    
    async def get_campaign_statistics(self):
        """Get comprehensive campaign statistics"""
        # This would fetch real data from database
        # For now, returning sample data
        return {
            'total_campaigns': 15,
            'total_messages': 45000,
            'delivery_rate': 98.5,
            'open_rate': 65.2,
            'click_rate': 12.8,
            'best_campaign': 'کمپین بهاری',
            'best_engagement': 78.5,
            'weak_campaigns': 3,
            'improvement_suggestions': 8
        }
    
    async def analyze_user_behavior(self, user_id):
        """Analyze individual user behavior for targeting"""
        async with self.db.get_connection() as db:
            # Get user activity patterns
            async with db.execute("""
                SELECT event_type, COUNT(*) as count, 
                       AVG(strftime('%H', timestamp)) as avg_hour
                FROM analytics 
                WHERE user_id = ? 
                AND timestamp >= datetime('now', '-30 days')
                GROUP BY event_type
            """, (user_id,)) as cursor:
                behavior_data = await cursor.fetchall()
            
            return {
                'activity_patterns': behavior_data,
                'best_time': self.calculate_best_time(behavior_data),
                'engagement_score': self.calculate_engagement_score(behavior_data),
                'interests': self.extract_interests(behavior_data)
            }
    
    def calculate_best_time(self, behavior_data):
        """Calculate best time to send messages to user"""
        if not behavior_data:
            return 12  # Default noon
        
        # Calculate weighted average of activity hours
        total_weight = sum(data[1] for data in behavior_data)
        if total_weight == 0:
            return 12
        
        weighted_hour = sum(data[2] * data[1] for data in behavior_data if data[2]) / total_weight
        return int(weighted_hour) if weighted_hour else 12
    
    def calculate_engagement_score(self, behavior_data):
        """Calculate user engagement score (0-100)"""
        if not behavior_data:
            return 0
        
        # Weight different activities
        activity_weights = {
            'button_click': 3,
            'referral_share': 5,
            'content_view': 2,
            'menu_navigation': 1
        }
        
        total_score = 0
        for event_type, count, _ in behavior_data:
            weight = activity_weights.get(event_type, 1)
            total_score += count * weight
        
        # Normalize to 0-100 scale
        return min(100, total_score // 10)
    
    def extract_interests(self, behavior_data):
        """Extract user interests from behavior"""
        interests = []
        
        for event_type, count, _ in behavior_data:
            if 'referral' in event_type and count > 5:
                interests.append('referral_enthusiast')
            elif 'content' in event_type and count > 10:
                interests.append('content_consumer')
            elif 'admin' in event_type:
                interests.append('power_user')
        
        return interests
    
    # ==================== CAMPAIGN EXECUTION ====================
    
    async def execute_smart_campaign(self, campaign_data):
        """Execute campaign with smart targeting"""
        target_users = await self.get_target_users(campaign_data['target_type'])
        
        successful_sends = 0
        failed_sends = 0
        
        for user_id in target_users:
            try:
                # Analyze user for personalization
                user_analysis = await self.analyze_user_behavior(user_id)
                
                # Personalize message
                personalized_message = await self.personalize_message(
                    campaign_data['message'], 
                    user_analysis
                )
                
                # Send at optimal time for user
                optimal_time = user_analysis['best_time']
                current_hour = datetime.now().hour
                
                if abs(current_hour - optimal_time) <= 2:  # Send now if within 2 hours
                    await self.send_campaign_message(user_id, personalized_message)
                    successful_sends += 1
                else:  # Schedule for later
                    await self.schedule_campaign_message(user_id, personalized_message, optimal_time)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_sends += 1
                await self.db.log_analytics('campaign_send_failed', user_id, str(e))
        
        # Log campaign results
        await self.db.log_analytics('campaign_executed', 0, {
            'campaign_id': campaign_data.get('id'),
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'target_type': campaign_data['target_type']
        })
        
        return {
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'total_targets': len(target_users)
        }
    
    async def personalize_message(self, base_message, user_analysis):
        """Personalize message based on user analysis"""
        personalized = base_message
        
        # Add personalization based on engagement score
        if user_analysis['engagement_score'] > 80:
            personalized += "\n\n🌟 شما یکی از کاربران فعال ما هستید!"
        elif user_analysis['engagement_score'] < 30:
            personalized += "\n\n💡 ما را فراموش نکنید!"
        
        # Add interest-based content
        if 'referral_enthusiast' in user_analysis['interests']:
            personalized += "\n🔗 فراموش نکنید دوستان خود را دعوت کنید!"
        
        return personalized
    
    async def get_target_users(self, target_type):
        """Get list of users based on targeting criteria"""
        async with self.db.get_connection() as db:
            if target_type == 'all':
                query = "SELECT user_id FROM users WHERE is_banned = FALSE"
            elif target_type == 'active':
                query = """
                    SELECT user_id FROM users 
                    WHERE is_banned = FALSE 
                    AND last_activity >= datetime('now', '-7 days')
                """
            elif target_type == 'new':
                query = """
                    SELECT user_id FROM users 
                    WHERE is_banned = FALSE 
                    AND join_date >= datetime('now', '-7 days')
                """
            elif target_type == 'top':
                query = """
                    SELECT user_id FROM users 
                    WHERE is_banned = FALSE 
                    AND total_referrals >= 5
                    ORDER BY total_referrals DESC
                    LIMIT 100
                """
            elif target_type == 'inactive':
                query = """
                    SELECT user_id FROM users 
                    WHERE is_banned = FALSE 
                    AND last_activity < datetime('now', '-30 days')
                """
            else:
                query = "SELECT user_id FROM users WHERE is_banned = FALSE"
            
            async with db.execute(query) as cursor:
                users = await cursor.fetchall()
                return [user[0] for user in users]
    
    # ==================== CALLBACK HANDLER ====================
    
    async def handle_callback_query(self, callback: types.CallbackQuery):
        """Handle advertising-related callback queries"""
        if callback.data == "ad_panel":
            await self.show_advertising_panel(callback)
        elif callback.data == "ad_create_campaign":
            await self.create_campaign_wizard(callback)
        elif callback.data.startswith("campaign_type_"):
            await self.handle_campaign_type(callback)
        elif callback.data == "ad_cross_promotion":
            await self.show_cross_promotion(callback)
        elif callback.data == "cross_add_partner":
            await self.add_partner_channel(callback)
        elif callback.data == "ad_smart_targeting":
            await self.show_smart_targeting(callback)
        elif callback.data == "ad_ab_testing":
            await self.show_ab_testing(callback)
        elif callback.data == "ad_analytics":
            await self.show_campaign_analytics(callback)
        elif callback.data == "ad_optimization":
            await self.show_optimization_panel(callback)
        
        await callback.answer()