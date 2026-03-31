"""Entry point for Meme Story Bot."""

from src.scheduler import Scheduler

if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.run()
