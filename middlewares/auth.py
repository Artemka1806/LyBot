from typing import Any, Callable, Dict, Awaitable, Optional
import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from models.user import User

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if hasattr(event, "callback_query") and event.callback_query and event.callback_query.data.startswith("nodb_"):
            return await handler(event, data)

        # Отримуємо telegram id користувача
        tg_id = self._extract_tg_id(event)
        
        if tg_id:
            try:
                # Переконуємося, що tg_id є цілим числом
                tg_id_int = int(tg_id)
                # Пошук користувача з явним вказанням типу
                user = await User.find_one({"tg_id": tg_id_int})
                
                if user:
                    logger.info(f"Користувача знайдено: {user.email}")
                else:
                    logger.warning(f"Користувача з tg_id={tg_id_int} не знайдено в базі даних")
                
                data["user"] = user
            except Exception as e:
                logger.error(f"Помилка при пошуку користувача: {str(e)}")
                data["user"] = None
        else:
            data["user"] = None
            
        return await handler(event, data)
    
    def _extract_tg_id(self, event) -> Optional[int]:
        """Витягує ID користувача з різних типів подій."""
        if hasattr(event, "callback_query") and event.callback_query:
            return event.callback_query.from_user.id
        elif hasattr(event, "message") and event.message:
            return event.message.from_user.id
        elif hasattr(event, "pre_checkout_query") and event.pre_checkout_query:
            return event.pre_checkout_query.from_user.id
        return None
