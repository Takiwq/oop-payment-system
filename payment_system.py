# ============================================
# Назва завдання: Платіжна система
# Опис: Клас PaymentSystem — реєстр рахунків та перекази
# ============================================

from __future__ import annotations

from typing import Optional

from models import Transaction, TransactionType, AccountStatus
from accounts import Account, SavingsAccount, CreditAccount, CurrencyAccount


class PaymentSystem:
    """
    Платіжна система — центральний реєстр усіх банківських рахунків.

    Відповідає за реєстрацію рахунків, пошук за номером,
    здійснення переказів між рахунками та загальну аналітику.

    Attributes:
        _name: Назва платіжної системи.
        _accounts: Словник {account_number: Account}.
    """

    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Назва платіжної системи не може бути порожньою.")
        self._name: str = name.strip()
        self._accounts: dict[str, Account] = {}

    # ---------- властивості ----------

    @property
    def name(self) -> str:
        return self._name

    # ---------- публічні методи ----------

    def register(self, account: Account) -> None:
        """
        Зареєструвати рахунок у системі.

        Args:
            account: Об'єкт Account (або підкласу).

        Raises:
            TypeError: Якщо передано не рахунок.
            ValueError: Якщо рахунок вже зареєстровано.
        """
        if not isinstance(account, Account):
            raise TypeError("Можна реєструвати тільки об'єкти Account.")
        number = account.account_number
        if number in self._accounts:
            raise ValueError(f"Рахунок {number} вже зареєстровано в системі.")
        self._accounts[number] = account

    def unregister(self, account_number: str) -> None:
        """
        Видалити рахунок із реєстру системи.

        Args:
            account_number: Номер рахунку.

        Raises:
            KeyError: Якщо рахунок не знайдено.
        """
        if account_number not in self._accounts:
            raise KeyError(f"Рахунок {account_number} не знайдено в системі.")
        del self._accounts[account_number]

    def transfer(
        self,
        from_acc: Account,
        to_acc: Account,
        amount: float,
        description: str = "",
    ) -> tuple[Transaction, Transaction]:
        """
        Переказати кошти між двома рахунками.

        Створює дві пов'язані транзакції:
        - TRANSFER_OUT на рахунку відправника,
        - TRANSFER_IN  на рахунку отримувача.

        Args:
            from_acc: Рахунок-відправник.
            to_acc:   Рахунок-отримувач.
            amount:   Сума переказу (> 0).
            description: Опис операції.

        Returns:
            Кортеж (транзакція_відправника, транзакція_отримувача).

        Raises:
            TypeError:  Якщо передано не рахунок.
            ValueError: Якщо рахунки однакові, сума <= 0,
                        або рахунок не зареєстровано в системі.
        """
        if not isinstance(from_acc, Account) or not isinstance(to_acc, Account):
            raise TypeError("Обидва аргументи мають бути об'єктами Account.")
        if from_acc == to_acc:
            raise ValueError("Рахунок-відправник і отримувач не можуть збігатися.")
        if not isinstance(amount, (int, float)):
            raise TypeError("Сума має бути числом.")
        if amount <= 0:
            raise ValueError("Сума переказу має бути більше 0.")

        for acc in (from_acc, to_acc):
            if acc.account_number not in self._accounts:
                raise ValueError(
                    f"Рахунок {acc.account_number} не зареєстровано в системі."
                )

        desc = description or (
            f"Переказ {amount:.2f} грн: "
            f"{from_acc.account_number} → {to_acc.account_number}"
        )

        # знімаємо з відправника (логіка перевірки ліміту — у самому класі)
        out_tx = from_acc.withdraw(
            amount,
            description=f"Переказ до {to_acc.account_number}. {desc}",
        )
        # змінюємо тип транзакції на TRANSFER_OUT (withdraw створює WITHDRAWAL)
        # Замість патчингу — просто фіксуємо окремою транзакцією TRANSFER_OUT
        out_transfer = Transaction(
            amount=amount,
            transaction_type=TransactionType.TRANSFER_OUT,
            description=f"Переказ до {to_acc.account_number}. {desc}",
        )
        # поповнюємо отримувача
        in_tx = to_acc.deposit(
            amount,
            description=f"Переказ від {from_acc.account_number}. {desc}",
        )
        in_transfer = Transaction(
            amount=amount,
            transaction_type=TransactionType.TRANSFER_IN,
            description=f"Переказ від {from_acc.account_number}. {desc}",
        )

        return out_transfer, in_transfer

    def find_by_owner_tax_id(self, tax_id: str) -> list[Account]:
        """
        Знайти всі рахунки за ІПН власника.

        Args:
            tax_id: ІПН (рядок з 10 цифр).

        Returns:
            Список рахунків цього власника.
        """
        return [
            acc for acc in self._accounts.values()
            if acc.owner.tax_id == tax_id
        ]

    def get_active_accounts(self) -> list[Account]:
        """Повернути список усіх активних рахунків."""
        return [
            acc for acc in self._accounts.values()
            if acc.status == AccountStatus.ACTIVE
        ]

    def get_total_assets(self) -> float:
        """
        Загальна сума активів у системі (сума балансів усіх активних рахунків).

        Returns:
            Сума балансів (від'ємні баланси кредитних рахунків включені).
        """
        return sum(
            acc.balance for acc in self._accounts.values()
            if acc.status == AccountStatus.ACTIVE
        )

    def get_summary(self) -> str:
        """
        Коротка зведена аналітика по системі.

        Returns:
            Рядок зі статистикою: кількість рахунків за типом та загальні активи.
        """
        total = len(self._accounts)
        active = len(self.get_active_accounts())
        savings = sum(1 for a in self._accounts.values() if type(a) is SavingsAccount)
        credit = sum(1 for a in self._accounts.values() if isinstance(a, CreditAccount))
        currency = sum(1 for a in self._accounts.values() if isinstance(a, CurrencyAccount))

        lines = [
            "=" * 50,
            f"  Платіжна система: {self._name}",
            f"  Усього рахунків:  {total}",
            f"    - активних:     {active}",
            f"    - ощадних:      {savings}",
            f"    - кредитних:    {credit}",
            f"    - валютних:     {currency}",
            f"  Загальні активи: {self.get_total_assets():.2f} грн",
            "=" * 50,
        ]
        return "\n".join(lines)

    # ---------- магічні методи ----------

    def __len__(self) -> int:
        """Кількість зареєстрованих рахунків."""
        return len(self._accounts)

    def __getitem__(self, account_number: str) -> Account:
        """
        Отримати рахунок за номером.

        Raises:
            KeyError: Якщо рахунок не знайдено.
        """
        if account_number not in self._accounts:
            raise KeyError(f"Рахунок {account_number} не знайдено.")
        return self._accounts[account_number]

    def __contains__(self, account_number: str) -> bool:
        """Перевірити, чи зареєстровано рахунок: `number in system`."""
        return account_number in self._accounts

    def __str__(self) -> str:
        active = len(self.get_active_accounts())
        return (
            f"PaymentSystem '{self._name}': "
            f"{len(self)} рахунків, {active} активних"
        )

    def __repr__(self) -> str:
        return (
            f"PaymentSystem(name='{self._name}', "
            f"accounts={len(self._accounts)})"
        )