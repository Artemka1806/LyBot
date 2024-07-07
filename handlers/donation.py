from typing import Type

from aiogram import Router, F, flags, Bot
from aiogram.filters import MagicData, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()
router.message.filter(MagicData(F.user))


class DonationAmount(StatesGroup):
	sets_amount = State()


@router.message(F.text == "⭐ Пожертвування")
async def donation_handler(message: Message, state: FSMContext, user: Type) -> None:
	await message.answer("Введіть кількість зірочок, які ви хочете пожертвувавти:\n\n/cancel для відміни")
	await state.set_state(DonationAmount.sets_amount)


@router.message(Command("cancel"), DonationAmount.sets_amount)
@flags.show_main_menu
async def cancel_command_handler(message: Message, state: FSMContext, user: Type) -> None:
	await state.clear()
	await message.answer("OK")


@router.message(F.text.regexp(r"^\d+$"), DonationAmount.sets_amount)
async def amount_selected(message: Message, state: FSMContext, user: Type) -> None:
	AMOUNT = int(message.text)
	kb = InlineKeyboardBuilder()
	kb.button(text=f"Пожервувати {AMOUNT} ⭐️", pay=True)

	prices = [LabeledPrice(label="XTR", amount=AMOUNT)]
	await message.answer_invoice(
		title="Пожертвування",
		description=f"Добровільне пожервування розміром в {AMOUNT} ⭐\n\nПовернення коштів не передбачається😁",
		prices=prices,
		provider_token="",
		payload="channel_support",
		currency="XTR",
		reply_markup=kb.as_markup()
	)
	await state.clear()


async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
	await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
@flags.show_main_menu
async def success_payment_handler(message: Message):
	await message.answer(text="🥳Дякую!🤗")


@router.message(Command("paysupport"))
@flags.show_main_menu
async def refund_payment_handler(message: Message, bot: Bot):
	payment_id = ""
	try:
		payment_id = message.text.split(" ")[1]
	except IndexError:
		await message.answer("Невірний ID платежа")
		return

	await bot.refund_star_payment(
		user_id=message.from_user.id,
		telegram_payment_charge_id=payment_id,
	)
	await message.answer(text="Успішно повернуто платіж 😭😭😭")


router.pre_checkout_query.register(pre_checkout_handler)
