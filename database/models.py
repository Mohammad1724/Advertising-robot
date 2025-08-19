import aiosqlite
from datetime import datetime
import json

class Database:
    def __init__(self, db_path="bot.db"):
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize database with all required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    referrer_id INTEGER,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_member BOOLEAN DEFAULT FALSE,
                    total_referrals INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 0,
                    is_banned BOOLEAN DEFAULT FALSE,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Referrals table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reward_given BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                    FOREIGN KEY (referred_id) REFERENCES users (user_id)
                )
            """)
            
            # Analytics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    user_id INTEGER,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Broadcast messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_text TEXT,
                    media_type TEXT,
                    media_file_id TEXT,
                    scheduled_time TIMESTAMP,
                    sent BOOLEAN DEFAULT FALSE,
                    total_sent INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Exclusive content table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS exclusive_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    file_id TEXT,
                    file_type TEXT,
                    required_referrals INTEGER DEFAULT 0,
                    required_points INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # User rewards table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    content_id INTEGER,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (content_id) REFERENCES exclusive_content (id)
                )
            """)
            
            await db.commit()
    
    async def add_user(self, user_id, username, first_name, last_name, referrer_id=None):
        """Add new user to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, referrer_id)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, referrer_id))
            await db.commit()
    
    async def get_user(self, user_id):
        """Get user data by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()
    
    async def update_user_activity(self, user_id):
        """Update user's last activity"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?
            """, (user_id,))
            await db.commit()
    
    async def update_membership(self, user_id, is_member):
        """Update user membership status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET is_member = ? WHERE user_id = ?
            """, (is_member, user_id))
            await db.commit()
    
    async def add_referral(self, referrer_id, referred_id):
        """Add referral and update points"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if referral already exists
            async with db.execute("""
                SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?
            """, (referrer_id, referred_id)) as cursor:
                existing = await cursor.fetchone()
            
            if not existing:
                await db.execute("""
                    INSERT INTO referrals (referrer_id, referred_id)
                    VALUES (?, ?)
                """, (referrer_id, referred_id))
                
                # Update referrer's stats
                await db.execute("""
                    UPDATE users 
                    SET total_referrals = total_referrals + 1,
                        points = points + 10
                    WHERE user_id = ?
                """, (referrer_id,))
                await db.commit()
                return True
            return False
    
    async def get_user_stats(self):
        """Get overall bot statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Total users
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                stats['total_users'] = (await cursor.fetchone())[0]
            
            # Active members
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_member = TRUE") as cursor:
                stats['active_members'] = (await cursor.fetchone())[0]
            
            # Today's new users
            async with db.execute("""
                SELECT COUNT(*) FROM users 
                WHERE DATE(join_date) = DATE('now')
            """) as cursor:
                stats['today_users'] = (await cursor.fetchone())[0]
            
            # Total referrals
            async with db.execute("SELECT COUNT(*) FROM referrals") as cursor:
                stats['total_referrals'] = (await cursor.fetchone())[0]
            
            # Active users (last 7 days)
            async with db.execute("""
                SELECT COUNT(*) FROM users 
                WHERE last_activity >= datetime('now', '-7 days')
            """) as cursor:
                stats['active_week'] = (await cursor.fetchone())[0]
            
            return stats
    
    async def get_top_referrers(self, limit=10):
        """Get top referrers leaderboard"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, first_name, total_referrals, points
                FROM users 
                WHERE total_referrals > 0
                ORDER BY total_referrals DESC, points DESC
                LIMIT ?
            """, (limit,)) as cursor:
                return await cursor.fetchall()
    
    async def get_all_users(self):
        """Get all users for broadcasting"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id FROM users WHERE is_banned = FALSE
            """) as cursor:
                return await cursor.fetchall()
    
    async def log_analytics(self, event_type, user_id, data=""):
        """Log analytics event"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO analytics (event_type, user_id, data)
                VALUES (?, ?, ?)
            """, (event_type, user_id, str(data)))
            await db.commit()
    
    async def add_exclusive_content(self, title, description, file_id, file_type, required_referrals=0, required_points=0):
        """Add exclusive content"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO exclusive_content 
                (title, description, file_id, file_type, required_referrals, required_points)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, description, file_id, file_type, required_referrals, required_points))
            await db.commit()
            return cursor.lastrowid
    
    async def get_available_content(self, user_referrals, user_points):
        """Get content available for user based on referrals and points"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT * FROM exclusive_content 
                WHERE is_active = TRUE 
                AND required_referrals <= ? 
                AND required_points <= ?
                ORDER BY required_referrals DESC, required_points DESC
            """, (user_referrals, user_points)) as cursor:
                return await cursor.fetchall()
    
    async def claim_reward(self, user_id, content_id):
        """Mark content as claimed by user"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if already claimed
            async with db.execute("""
                SELECT id FROM user_rewards WHERE user_id = ? AND content_id = ?
            """, (user_id, content_id)) as cursor:
                existing = await cursor.fetchone()
            
            if not existing:
                await db.execute("""
                    INSERT INTO user_rewards (user_id, content_id)
                    VALUES (?, ?)
                """, (user_id, content_id))
                await db.commit()
                return True
            return False