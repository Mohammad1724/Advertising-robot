from datetime import datetime, timedelta
import json

class Analytics:
    def __init__(self, db):
        self.db = db
    
    async def track_user_action(self, user_id, action, data=None):
        """Track user action for analytics"""
        await self.db.log_analytics(action, user_id, data or {})
    
    async def get_user_growth_stats(self, days=30):
        """Get user growth statistics for specified days"""
        async with self.db.get_connection() as db:
            stats = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                
                async with db.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE DATE(join_date) = ?
                """, (date_str,)) as cursor:
                    count = (await cursor.fetchone())[0]
                
                stats.append({
                    'date': date_str,
                    'new_users': count
                })
            
            return list(reversed(stats))
    
    async def get_referral_stats(self):
        """Get referral system statistics"""
        async with self.db.get_connection() as db:
            stats = {}
            
            # Total referrals
            async with db.execute("SELECT COUNT(*) FROM referrals") as cursor:
                stats['total_referrals'] = (await cursor.fetchone())[0]
            
            # Average referrals per user
            async with db.execute("""
                SELECT AVG(total_referrals) FROM users WHERE total_referrals > 0
            """) as cursor:
                avg = await cursor.fetchone()
                stats['avg_referrals'] = round(avg[0] if avg[0] else 0, 2)
            
            # Top referrer
            async with db.execute("""
                SELECT first_name, total_referrals FROM users 
                ORDER BY total_referrals DESC LIMIT 1
            """) as cursor:
                top = await cursor.fetchone()
                stats['top_referrer'] = {
                    'name': top[0] if top else 'None',
                    'count': top[1] if top else 0
                }
            
            # Referrals this week
            async with db.execute("""
                SELECT COUNT(*) FROM referrals 
                WHERE date >= datetime('now', '-7 days')
            """) as cursor:
                stats['week_referrals'] = (await cursor.fetchone())[0]
            
            return stats
    
    async def get_activity_stats(self):
        """Get user activity statistics"""
        async with self.db.get_connection() as db:
            stats = {}
            
            # Active users (last 24 hours)
            async with db.execute("""
                SELECT COUNT(*) FROM users 
                WHERE last_activity >= datetime('now', '-1 day')
            """) as cursor:
                stats['daily_active'] = (await cursor.fetchone())[0]
            
            # Active users (last 7 days)
            async with db.execute("""
                SELECT COUNT(*) FROM users 
                WHERE last_activity >= datetime('now', '-7 days')
            """) as cursor:
                stats['weekly_active'] = (await cursor.fetchone())[0]
            
            # Active users (last 30 days)
            async with db.execute("""
                SELECT COUNT(*) FROM users 
                WHERE last_activity >= datetime('now', '-30 days')
            """) as cursor:
                stats['monthly_active'] = (await cursor.fetchone())[0]
            
            return stats
    
    async def get_popular_actions(self, limit=10):
        """Get most popular user actions"""
        async with self.db.get_connection() as db:
            async with db.execute("""
                SELECT event_type, COUNT(*) as count
                FROM analytics 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT ?
            """, (limit,)) as cursor:
                return await cursor.fetchall()
    
    async def get_hourly_activity(self):
        """Get hourly activity distribution"""
        async with self.db.get_connection() as db:
            hourly_stats = {}
            
            for hour in range(24):
                async with db.execute("""
                    SELECT COUNT(*) FROM analytics 
                    WHERE strftime('%H', timestamp) = ? 
                    AND timestamp >= datetime('now', '-7 days')
                """, (f"{hour:02d}",)) as cursor:
                    count = (await cursor.fetchone())[0]
                    hourly_stats[hour] = count
            
            return hourly_stats
    
    async def generate_analytics_report(self):
        """Generate comprehensive analytics report"""
        user_stats = await self.db.get_user_stats()
        referral_stats = await self.get_referral_stats()
        activity_stats = await self.get_activity_stats()
        popular_actions = await self.get_popular_actions(5)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'user_stats': user_stats,
            'referral_stats': referral_stats,
            'activity_stats': activity_stats,
            'popular_actions': dict(popular_actions),
            'summary': {
                'growth_rate': self._calculate_growth_rate(user_stats),
                'engagement_rate': self._calculate_engagement_rate(user_stats, activity_stats)
            }
        }
        
        return report
    
    def _calculate_growth_rate(self, user_stats):
        """Calculate user growth rate"""
        if user_stats['total_users'] == 0:
            return 0
        return round((user_stats['today_users'] / user_stats['total_users']) * 100, 2)
    
    def _calculate_engagement_rate(self, user_stats, activity_stats):
        """Calculate user engagement rate"""
        if user_stats['total_users'] == 0:
            return 0
        return round((activity_stats['daily_active'] / user_stats['total_users']) * 100, 2)