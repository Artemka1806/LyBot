from .admin import router as AdminRouter
from .attendance import router as AttendanceRouter
from .donation import router as DonationRouter
from .group import router as GroupRouter
from .login import router as LoginRouter
from .schedule import router as ScheduleRouter
from .settings import router as SettingsRouter

ROUTERS = (
	AdminRouter,
	AttendanceRouter, DonationRouter,
	GroupRouter,
	ScheduleRouter,
	SettingsRouter,
    LoginRouter
)
