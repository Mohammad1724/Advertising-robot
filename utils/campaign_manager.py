import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json

class CampaignManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.active_campaigns = {}
        self.ab_tests = {}
    
    def start(self):
        """Start campaign manager"""
        self.scheduler.start()
        self.setup_campaign_jobs()
    
    def stop(self):
        """Stop campaign manager"""
        self.scheduler.shutdown()
    
    def setup_campaign_jobs(self):
        """Setup scheduled campaign jobs"""
        # Check for scheduled campaigns every minute
        self.scheduler.add_job(
            self.check_scheduled_campaigns,
            'interval',
            minutes=1,
            id='check_campaigns'
        )
        
        # Optimize campaigns daily
        self.scheduler.add_job(
            self.daily_campaign_optimization,
            'cron',
            hour=2,
            minute=0,
            id='daily_optimization'
        )
        
        # Generate campaign reports weekly
        self.scheduler.add_job(
            self.weekly_campaign_report,
            'cron',
            day_of_week=0,
            hour=9,
            minute=0,
            id='weekly_report'
        )
    
    async def check_scheduled_campaigns(self):
        """Check and execute scheduled campaigns"""
        try:
            current_time = datetime.now()
            
            # Get campaigns scheduled for current time
            async with self.db.get_connection() as db:
                async with db.execute("""
                    SELECT * FROM scheduled_campaigns 
                    WHERE scheduled_time <= ? 
                    AND executed = FALSE
                """, (current_time,)) as cursor:
                    campaigns = await cursor.fetchall()
            
            for campaign in campaigns:
                await self.execute_scheduled_campaign(campaign)
                
        except Exception as e:
            print(f"Error checking scheduled campaigns: {e}")
    
    async def execute_scheduled_campaign(self, campaign_data):
        """Execute a scheduled campaign"""
        try:
            campaign_id = campaign_data[0]
            
            # Mark as executed
            async with self.db.get_connection() as db:
                await db.execute("""
                    UPDATE scheduled_campaigns 
                    SET executed = TRUE, executed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (campaign_id,))
                await db.commit()
            
            # Execute the campaign
            await self.run_campaign(campaign_data)
            
        except Exception as e:
            print(f"Error executing campaign {campaign_id}: {e}")
    
    async def daily_campaign_optimization(self):
        """Daily optimization of active campaigns"""
        try:
            # Analyze yesterday's performance
            yesterday = datetime.now() - timedelta(days=1)
            
            # Get campaign performance data
            performance_data = await self.get_campaign_performance(yesterday)
            
            # Apply optimizations
            optimizations = await self.generate_optimizations(performance_data)
            
            # Send optimization report to admin
            await self.send_optimization_report(optimizations)
            
        except Exception as e:
            print(f"Error in daily optimization: {e}")
    
    async def get_campaign_performance(self, date):
        """Get campaign performance for specific date"""
        async with self.db.get_connection() as db:
            async with db.execute("""
                SELECT campaign_id, 
                       COUNT(*) as total_sent,
                       SUM(CASE WHEN delivered = 1 THEN 1 ELSE 0 END) as delivered,
                       SUM(CASE WHEN opened = 1 THEN 1 ELSE 0 END) as opened,
                       SUM(CASE WHEN clicked = 1 THEN 1 ELSE 0 END) as clicked
                FROM campaign_messages 
                WHERE DATE(sent_at) = DATE(?)
                GROUP BY campaign_id
            """, (date,)) as cursor:
                return await cursor.fetchall()
    
    async def generate_optimizations(self, performance_data):
        """Generate optimization suggestions"""
        optimizations = []
        
        for campaign in performance_data:
            campaign_id, total_sent, delivered, opened, clicked = campaign
            
            if total_sent > 0:
                delivery_rate = (delivered / total_sent) * 100
                open_rate = (opened / delivered) * 100 if delivered > 0 else 0
                click_rate = (clicked / opened) * 100 if opened > 0 else 0
                
                # Generate suggestions based on performance
                if delivery_rate < 95:
                    optimizations.append({
                        'campaign_id': campaign_id,
                        'type': 'delivery',
                        'suggestion': 'بهبود زمان‌بندی ارسال برای افزایش نرخ تحویل'
                    })
                
                if open_rate < 50:
                    optimizations.append({
                        'campaign_id': campaign_id,
                        'type': 'open_rate',
                        'suggestion': 'بهبود عنوان و محتوای پیام برای افزایش نرخ باز کردن'
                    })
                
                if click_rate < 10:
                    optimizations.append({
                        'campaign_id': campaign_id,
                        'type': 'click_rate',
                        'suggestion': 'بهبود دکمه‌های عمل (CTA) برای افزایش کلیک'
                    })
        
        return optimizations