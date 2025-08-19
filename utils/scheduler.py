from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import asyncio

class BotScheduler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        self.setup_jobs()
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
    
    def setup_jobs(self):
        """Setup scheduled jobs"""
        # Daily stats update
        self.scheduler.add_job(
            self.daily_stats_update,
            CronTrigger(hour=0, minute=0),
            id='daily_stats'
        )
        
        # Weekly leaderboard update
        self.scheduler.add_job(
            self.weekly_leaderboard,
            CronTrigger(day_of_week=0, hour=12, minute=0),
            id='weekly_leaderboard'
        )
        
        # Clean old analytics data
        self.scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(day=1, hour=2, minute=0),
            id='cleanup_data'
        )
        
        # Check pending broadcasts
        self.scheduler.add_job(
            self.check_pending_broadcasts,
            'interval',
            minutes=5,
            id='check_broadcasts'
        )
    
    async def daily_stats_update(self):
        """Update daily statistics"""
        try:
            stats = await self.db.get_user_stats()
            await self.db.log_analytics('daily_stats', 0, stats)
            print(f"Daily stats updated: {stats}")
        except Exception as e:
            print(f"Error updating daily stats: {e}")
    
    async def weekly_leaderboard(self):
        """Send weekly leaderboard to admin"""
        try:
            from config import ADMIN_ID
            top_users = await self.db.get_top_referrers(10)
            
            if top_users:
                text = "📊 گزارش هفتگی - برترین کاربران:\n\n"
                for i, user in enumerate(top_users, 1):
                    text += f"{i}. {user[1]} - {user[2]} دعوت\n"
                
                await self.bot.send_message(ADMIN_ID, text)
        except Exception as e:
            print(f"Error sending weekly leaderboard: {e}")
    
    async def cleanup_old_data(self):
        """Clean old analytics data (older than 3 months)"""
        try:
            async with self.db.get_connection() as db:
                await db.execute("""
                    DELETE FROM analytics 
                    WHERE timestamp < datetime('now', '-3 months')
                """)
                await db.commit()
            print("Old analytics data cleaned up")
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
    
    async def check_pending_broadcasts(self):
        """Check and send pending broadcast messages"""
        try:
            # This will be implemented in broadcast system
            pass
        except Exception as e:
            print(f"Error checking pending broadcasts: {e}")
    
    def schedule_broadcast(self, broadcast_id, send_time):
        """Schedule a broadcast message"""
        self.scheduler.add_job(
            self.send_scheduled_broadcast,
            'date',
            run_date=send_time,
            args=[broadcast_id],
            id=f'broadcast_{broadcast_id}'
        )
    
    async def send_scheduled_broadcast(self, broadcast_id):
        """Send scheduled broadcast message"""
        try:
            # Implementation will be added in broadcast handler
            print(f"Sending scheduled broadcast {broadcast_id}")
        except Exception as e:
            print(f"Error sending scheduled broadcast: {e}")