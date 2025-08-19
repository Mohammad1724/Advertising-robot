import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class ABTestManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.active_tests = {}
    
    async def create_ab_test(self, test_config: Dict[str, Any]):
        """Create new A/B test"""
        test_id = await self.save_test_config(test_config)
        
        # Split audience
        test_groups = await self.split_audience(
            test_config['audience_size'],
            test_config['split_ratio']
        )
        
        # Store test groups
        await self.save_test_groups(test_id, test_groups)
        
        return test_id
    
    async def split_audience(self, audience_size: int, split_ratio: float = 0.5):
        """Split audience into test groups"""
        # Get random sample of users
        async with self.db.get_connection() as db:
            async with db.execute("""
                SELECT user_id FROM users 
                WHERE is_banned = FALSE 
                AND is_member = TRUE
                ORDER BY RANDOM()
                LIMIT ?
            """, (audience_size,)) as cursor:
                users = await cursor.fetchall()
        
        user_ids = [user[0] for user in users]
        random.shuffle(user_ids)
        
        split_point = int(len(user_ids) * split_ratio)
        
        return {
            'group_a': user_ids[:split_point],
            'group_b': user_ids[split_point:]
        }
    
    async def run_ab_test(self, test_id: int):
        """Execute A/B test"""
        # Get test configuration
        test_config = await self.get_test_config(test_id)
        test_groups = await self.get_test_groups(test_id)
        
        # Send variant A to group A
        await self.send_test_variant(
            test_groups['group_a'],
            test_config['variant_a'],
            test_id,
            'A'
        )
        
        # Send variant B to group B
        await self.send_test_variant(
            test_groups['group_b'],
            test_config['variant_b'],
            test_id,
            'B'
        )
        
        # Schedule result analysis
        await self.schedule_result_analysis(test_id, test_config['duration'])
    
    async def send_test_variant(self, user_ids: List[int], variant: Dict, test_id: int, group: str):
        """Send test variant to specific group"""
        for user_id in user_ids:
            try:
                # Send message based on variant type
                if variant['type'] == 'text':
                    await self.bot.send_message(user_id, variant['content'])
                elif variant['type'] == 'photo':
                    await self.bot.send_photo(
                        user_id, 
                        variant['file_id'], 
                        caption=variant['caption']
                    )
                
                # Log test message
                await self.log_test_message(test_id, user_id, group, variant)
                
            except Exception as e:
                print(f"Failed to send test message to {user_id}: {e}")
    
    async def analyze_test_results(self, test_id: int):
        """Analyze A/B test results"""
        # Get test metrics
        metrics_a = await self.get_group_metrics(test_id, 'A')
        metrics_b = await self.get_group_metrics(test_id, 'B')
        
        # Calculate statistical significance
        significance = self.calculate_statistical_significance(metrics_a, metrics_b)
        
        # Determine winner
        winner = self.determine_winner(metrics_a, metrics_b, significance)
        
        # Save results
        results = {
            'test_id': test_id,
            'group_a_metrics': metrics_a,
            'group_b_metrics': metrics_b,
            'statistical_significance': significance,
            'winner': winner,
            'confidence_level': significance['confidence_level'],
            'analyzed_at': datetime.now().isoformat()
        }
        
        await self.save_test_results(test_id, results)
        
        return results
    
    async def get_group_metrics(self, test_id: int, group: str):
        """Get metrics for specific test group"""
        async with self.db.get_connection() as db:
            # Get basic metrics
            async with db.execute("""
                SELECT 
                    COUNT(*) as total_sent,
                    SUM(CASE WHEN delivered = 1 THEN 1 ELSE 0 END) as delivered,
                    SUM(CASE WHEN opened = 1 THEN 1 ELSE 0 END) as opened,
                    SUM(CASE WHEN clicked = 1 THEN 1 ELSE 0 END) as clicked,
                    AVG(engagement_time) as avg_engagement_time
                FROM ab_test_messages 
                WHERE test_id = ? AND test_group = ?
            """, (test_id, group)) as cursor:
                metrics = await cursor.fetchone()
        
        total_sent, delivered, opened, clicked, avg_engagement = metrics
        
        return {
            'total_sent': total_sent,
            'delivered': delivered,
            'opened': opened,
            'clicked': clicked,
            'delivery_rate': (delivered / total_sent * 100) if total_sent > 0 else 0,
            'open_rate': (opened / delivered * 100) if delivered > 0 else 0,
            'click_rate': (clicked / opened * 100) if opened > 0 else 0,
            'avg_engagement_time': avg_engagement or 0
        }
    
    def calculate_statistical_significance(self, metrics_a: Dict, metrics_b: Dict):
        """Calculate statistical significance between two groups"""
        # Simplified statistical significance calculation
        # In production, use proper statistical libraries like scipy
        
        n_a = metrics_a['total_sent']
        n_b = metrics_b['total_sent']
        
        if n_a < 30 or n_b < 30:
            return {
                'is_significant': False,
                'confidence_level': 0,
                'reason': 'Sample size too small (minimum 30 per group)'
            }
        
        # Compare click rates (main metric)
        rate_a = metrics_a['click_rate']
        rate_b = metrics_b['click_rate']
        
        # Simple difference calculation
        difference = abs(rate_a - rate_b)
        
        if difference > 2:  # 2% difference threshold
            confidence = min(95, difference * 10)  # Simplified confidence calculation
            return {
                'is_significant': True,
                'confidence_level': confidence,
                'difference': difference,
                'better_group': 'A' if rate_a > rate_b else 'B'
            }
        else:
            return {
                'is_significant': False,
                'confidence_level': 0,
                'difference': difference,
                'reason': 'Difference not significant enough'
            }
    
    def determine_winner(self, metrics_a: Dict, metrics_b: Dict, significance: Dict):
        """Determine the winning variant"""
        if not significance['is_significant']:
            return {
                'winner': 'No clear winner',
                'reason': significance.get('reason', 'Not statistically significant')
            }
        
        winner_group = significance['better_group']
        winner_metrics = metrics_a if winner_group == 'A' else metrics_b
        
        return {
            'winner': f'Variant {winner_group}',
            'improvement': significance['difference'],
            'confidence': significance['confidence_level'],
            'winning_metrics': winner_metrics
        }