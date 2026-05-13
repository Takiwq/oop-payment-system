# ============================================
# Назва завдання: Платіжна система
# Опис: Базові моделі - Owner, Transaction, Enum-типи
# ============================================

from __future__ import annotations
from enum import Enum
from datetime import datetime
from typing import Optional


class TransactionType(Enum):
    """Тип транзакції."""
    DEPOSIT = "поповнення"
    WITHDRAWAL = "зняття"
    TRANSFER_IN = "переказ (отримання)"
    TRANSFER_OUT = "переказ (відправлення)"
    INTEREST = "нарахування відсотків"
    FEE = "комісія"


class TransactionStatus(Enum):
    """Статус транзакції."""
    PENDING = "очікує"
    COMPLETED = "виконана"
    FAILED = "відхилена"
    CANCELLED = "скасована"


class AccountStatus(Enum):
    """Статус рахунку."""
    ACTIVE = "активний"
    BLOCKED = "заблокований"
    CLOSED = "закритий"


class Transaction:
    """
    Представляє одну фінансову операцію.

    Attributes:
        amount: Сума транзакції (завжди додатня).
        transaction_type: Тип операції (TransactionType).
        status: Статус операції (TransactionStatus).
        description: Опис транзакції.
        created_at: Дата та час створення.
    """

    def __init__(
        self,
        amount: float,
        transaction_type: TransactionType,
        description: str = "",
        status: TransactionStatus = TransactionStatus.COMPLETED,
    ) -> None:
        if not isinstance(amount, (int, float)):
            raise TypeError("Сума має бути числом.")
        if amount <= 0:
            raise ValueError("Сума транзакції має бути більше 0.")
        if not isinstance(transaction_type, TransactionType):
            raise TypeError("Тип транзакції має бути TransactionType.")

        self._amount: float = float(amount)
        self._transaction_type: TransactionType = transaction_type
        self._status: TransactionStatus = status
        self._description: str = description
        self._created_at: datetime = datetime.now()

    # ---------- властивості ----------

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def transaction_type(self) -> TransactionType:
        return self._transaction_type

    @property
    def status(self) -> TransactionStatus:
        return self._status

    @status.setter
    def status(self, value: TransactionStatus) -> None:
        if not isinstance(value, TransactionStatus):
            raise TypeError("Статус має бути TransactionStatus.")
        self._status = value

    @property
    def description(self) -> str:
        return self._description

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # ---------- магічні методи ----------

    def __str__(self) -> str:
        """Читабельний рядок для виписки."""
        date_str = self._created_at.strftime("%d.%m.%Y %H:%M")
        return (
            f"[{date_str}] {self._transaction_type.value:30s} "
            f"{self._amount:>10.2f} грн  |  {self._status.value}"
        )

    def __repr__(self) -> str:
        return (
            f"Transaction(amount={self._amount}, "
            f"type={self._transaction_type.name}, "
            f"status={self._status.name})"
        )

    def __eq__(self, other: object) -> bool:
        """Рівність — однаковий час, сума і тип."""
        if not isinstance(other, Transaction):
            return NotImplemented
        return (
            self._amount == other._amount
            and self._transaction_type == other._transaction_type
            and self._created_at == other._created_at
        )

    def __lt__(self, other: Transaction) -> bool:
        """Порівняння за датою — для сортування виписки."""
        if not isinstance(other, Transaction):
            return NotImplemented
        return self._created_at < other._created_at


class Owner:
    """
    Власник банківських рахунків.

    Attributes:
        full_name: ПІБ.
        tax_id: ІПН — рядок рівно з 10 цифр.
        phone: Контактний телефон.
    """

    def __init__(self, full_name: str, tax_id: str, phone: str = "") -> None:
        if not isinstance(full_name, str) or not full_name.strip():
            raise ValueError("ПІБ не може бути порожнім рядком.")
        if not isinstance(tax_id, str) or not tax_id.isdigit() or len(tax_id) != 10:
            raise ValueError("ІПН має бути рядком з рівно 10 цифр.")

        self._full_name: str = full_name.strip()
        self._tax_id: str = tax_id
        self._phone: str = phone
        # список номерів рахунків, прив'язаних до власника
        self._account_numbers: list[str] = []

    # ---------- властивості ----------

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def tax_id(self) -> str:
        return self._tax_id

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def account_numbers(self) -> list[str]:
        """Копія списку номерів рахунків (захист від зовнішньої зміни)."""
        return list(self._account_numbers)

    # ---------- публічні методи ----------

    def add_account(self, account_number: str) -> None:
        """Прив'язати номер рахунку до власника."""
        if account_number not in self._account_numbers:
            self._account_numbers.append(account_number)

    def remove_account(self, account_number: str) -> None:
        """Відв'язати номер рахунку від власника."""
        if account_number in self._account_numbers:
            self._account_numbers.remove(account_number)

    # ---------- магічні методи ----------

    def __str__(self) -> str:
        return f"{self._full_name} (ІПН: {self._tax_id})"

    def __repr__(self) -> str:
        return f"Owner(full_name='{self._full_name}', tax_id='{self._tax_id}')"

    def __eq__(self, other: object) -> bool:
        """Двоє власників рівні, якщо збігається ІПН."""
        if not isinstance(other, Owner):
            return NotImplemented
        return self._tax_id == other._tax_id

    def __hash__(self) -> int:
        """Хешування за ІПН - щоб можна було використовувати як ключ словника."""
        return hash(self._tax_id)
