from .attendance import router as AttendanceRouter
from .donation import router as DonationRouter
from .login import router as LoginRouter
from .schedule import router as ScheduleRouter

ROUTERS = (
	AttendanceRouter, DonationRouter,
	LoginRouter, ScheduleRouter
)
