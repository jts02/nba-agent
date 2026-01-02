"""
Job scheduler for running agent tasks periodically.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from datetime import datetime

from agents import TweetMonitorAgent, BoxScoreAgent


class JobScheduler:
    """Scheduler for running periodic tasks."""
    
    def __init__(
        self,
        tweet_monitor: TweetMonitorAgent = None,
        box_score_agent: BoxScoreAgent = None,
        tweet_check_interval_minutes: int = 5,
        box_score_post_interval_minutes: int = 60
    ):
        """
        Initialize the job scheduler.
        
        Args:
            tweet_monitor: Tweet monitoring agent (optional)
            box_score_agent: Box score posting agent (optional)
            tweet_check_interval_minutes: How often to check for new tweets
            box_score_post_interval_minutes: How often to post box scores
        """
        self.tweet_monitor = tweet_monitor
        self.box_score_agent = box_score_agent
        self.tweet_check_interval = tweet_check_interval_minutes
        self.box_score_interval = box_score_post_interval_minutes
        
        self.scheduler = BackgroundScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Set up scheduled jobs."""
        jobs_scheduled = []
        
        # Tweet monitoring job (if enabled)
        if self.tweet_monitor:
            self.scheduler.add_job(
                func=self._tweet_monitor_job,
                trigger=IntervalTrigger(minutes=self.tweet_check_interval),
                id='tweet_monitor',
                name='Monitor tweets for injuries',
                replace_existing=True
            )
            jobs_scheduled.append(f"tweet monitoring every {self.tweet_check_interval} min")
        
        # Box score posting job (if enabled)
        if self.box_score_agent:
            self.scheduler.add_job(
                func=self._box_score_job,
                trigger=IntervalTrigger(minutes=self.box_score_interval),
                id='box_score_poster',
                name='Post NBA box scores',
                replace_existing=True
            )
            jobs_scheduled.append(f"box scores every {self.box_score_interval} min")
        
        if jobs_scheduled:
            logger.info(f"Scheduled jobs: {', '.join(jobs_scheduled)}")
        else:
            logger.warning("No jobs scheduled!")
    
    def _tweet_monitor_job(self):
        """Job wrapper for tweet monitoring."""
        if not self.tweet_monitor:
            logger.warning("Tweet monitor job triggered but no tweet monitor configured")
            return
        try:
            logger.info(f"[{datetime.now()}] Running tweet monitor job")
            self.tweet_monitor.process_new_tweets()
        except Exception as e:
            logger.error(f"Error in tweet monitor job: {e}", exc_info=True)
    
    def _box_score_job(self):
        """Job wrapper for box score posting."""
        if not self.box_score_agent:
            logger.warning("Box score job triggered but no box score agent configured")
            return
        try:
            logger.info(f"[{datetime.now()}] Running box score job")
            self.box_score_agent.post_recent_box_scores()
        except Exception as e:
            logger.error(f"Error in box score job: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            
            # Run initial jobs immediately
            logger.info("Running initial jobs...")
            if self.tweet_monitor:
                self._tweet_monitor_job()
            if self.box_score_agent:
                self._box_score_job()
        else:
            logger.warning("Scheduler is already running")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler is not running")
    
    def get_job_status(self):
        """Get status of all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        status = []
        
        for job in jobs:
            status.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
            })
        
        return status

