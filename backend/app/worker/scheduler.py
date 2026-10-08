from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import structlog
from app.database import SessionLocal
from app.services.ingestion import IngestionService

logger = structlog.get_logger(__name__)

def update_quotes():
    logger.info("worker_update_quotes_start")
    db = SessionLocal()
    try:
        svc = IngestionService(db)
        svc.refresh_quotes()
        logger.info("worker_update_quotes_success")
    except Exception as e:
        logger.error("worker_update_quotes_error", error=str(e))
    finally:
        db.close()

def update_daily_candles():
    logger.info("worker_update_candles_start")
    db = SessionLocal()
    try:
        svc = IngestionService(db)
        svc.refresh_daily_candles()
        logger.info("worker_update_candles_success")
    except Exception as e:
        logger.error("worker_update_candles_error", error=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone='Asia/Kolkata')
    
    # Quotes: Every 5 mins during market hours (9:15 - 15:30 IST)
    scheduler.add_job(
        update_quotes,
        trigger=CronTrigger(day_of_week='mon-fri', hour='9-15', minute='*/5'),
        id='update_quotes',
        replace_existing=True
    )
    
    # Daily Candles: 6 PM IST daily
    scheduler.add_job(
        update_daily_candles,
        trigger=CronTrigger(day_of_week='mon-fri', hour='18', minute='0'),
        id='update_daily_candles',
        replace_existing=True
    )
    
    logger.info("worker_started")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
