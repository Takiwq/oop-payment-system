# ============================================
# Назва завдання: Платіжна система
# Опис: Абстрактний клас Account та конкретні типи рахунків
# ============================================

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
import uuid

from models import (
    Owner,
    Transaction,
    TransactionType,
    TransactionStatus,
    AccountStatus,
)


class Account(ABC):
    """
    Абстрактний базовий клас банківського рахунку.

    Визначає спільний інтерфейс для всіх типів рахунків:
    номер, баланс, власник, список транзакцій та статус.

    Attributes:
        account_number: Унікальний номер рахунку (генерується автоматично).
        owner: Власник рахунку (об'єкт Owner).
        _balance: Поточний баланс (захищений атрибут).
        _status: Статус рахунку (AccountStatus).
        _transactions: Історія транзакцій.
    """

    def __init__(self, owner: Owner, initial_balance: float = 0.0) -> None:
        if not isinstance(owner, Owner):
            raise TypeError("Власник має бути об'єктом Owner.")
        if not isinstance(initial_balance, (int, float)):
            raise TypeError("Початковий баланс має бути числом.")
        if initial_balance < 0:
            raise ValueError("Початковий баланс не може бути від'ємним.")

        self._account_number: str = self._generate_account_number()
        self._owner: Owner = owner
        self._balance: float = float(initial_balance)
        self._status: AccountStatus = AccountStatus.ACTIVE
        self._transactions: list[Transaction] = []

        # прив'язуємо рахунок до власника
        owner.add_account(self._account_number)

    # ---------- службові методи ----------

    @staticmethod
    def _generate_account_number() -> str:
        """Генерує унікальний номер рахунку у форматі UA + 16 цифр."""
        digits = uuid.uuid4().int % (10 ** 16)
        return f"UA{digits:016d}"

    def _check_active(self) -> None:
        """Перевіряє, що рахунок активний. Інакше — ValueError."""
        if self._status == AccountStatus.BLOCKED:
            raise ValueError(f"Рахунок {self._account_number} заблокований.")
        if self._status == AccountStatus.CLOSED:
            raise ValueError(f"Рахунок {self._account_number} закритий.")

    def _add_transaction(self, transaction: Transaction) -> None:
        """Додає транзакцію до історії."""
        self._transactions.append(transaction)

    # ---------- властивості ----------

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def owner(self) -> Owner:
        return self._owner

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def status(self) -> AccountStatus:
        return self._status

    @property
    def transactions(self) -> list[Transaction]:
        """Копія списку транзакцій (захист від зовнішньої зміни)."""
        return list(self._transactions)

    # ---------- публічні методи ----------

    def deposit(self, amount: float, description: str = "") -> Transaction:
        """
        Поповнити рахунок на вказану суму.

        Args:
            amount: Сума поповнення (> 0).
            description: Опис операції.

        Returns:
            Об'єкт Transaction зі статусом COMPLETED.

        Raises:
            ValueError: Якщо рахунок не активний або сума <= 0.
            TypeError: Якщо сума не є числом.
        """
        self._check_active()
        if not isinstance(amount, (int, float)):
            raise TypeError("Сума має бути числом.")
        if amount <= 0:
            raise ValueError("Сума поповнення має бути більше 0.")

        self._balance += amount
        transaction = Transaction(
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            description=description or f"Поповнення рахунку {self._account_number}",
        )
        self._add_transaction(transaction)
        return transaction

    @abstractmethod
    def withdraw(self, amount: float, description: str = "") -> Transaction:
        """
        Зняти кошти з рахунку.
        Логіка залежить від типу рахунку — реалізується у підкласах.

        Args:
            amount: Сума зняття (> 0).
            description: Опис операції.

        Returns:
            Об'єкт Transaction.
        """

    @abstractmethod
    def get_statement(self) -> str:
        """
        Повернути виписку по рахунку у вигляді рядка.
        Формат залежить від типу рахунку.
        """

    def block(self) -> None:
        """Заблокувати рахунок."""
        if self._status == AccountStatus.CLOSED:
            raise ValueError("Неможливо заблокувати закритий рахунок.")
        self._status = AccountStatus.BLOCKED
        print(f"Рахунок {self._account_number} заблоковано.")

    def unblock(self) -> None:
        """Розблокувати рахунок."""
        if self._status != AccountStatus.BLOCKED:
            raise ValueError("Рахунок не є заблокованим.")
        self._status = AccountStatus.ACTIVE
        print(f"Рахунок {self._account_number} розблоковано.")

    def close(self) -> None:
        """Закрити рахунок (тільки при нульовому балансі)."""
        if self._balance != 0:
            raise ValueError("Неможливо закрити рахунок з ненульовим балансом.")
        self._status = AccountStatus.CLOSED
        self._owner.remove_account(self._account_number)
        print(f"Рахунок {self._account_number} закрито.")

    # ---------- магічні методи ----------

    def __str__(self) -> str:
        return (
            f"Рахунок {self._account_number} | "
            f"Власник: {self._owner.full_name} | "
            f"Баланс: {self._balance:.2f} грн | "
            f"Статус: {self._status.value}"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"account_number='{self._account_number}', "
            f"balance={self._balance}, "
            f"status={self._status.name})"
        )

    def __eq__(self, other: object) -> bool:
        """Два рахунки рівні, якщо збігаються їх номери."""
        if not isinstance(other, Account):
            return NotImplemented
        return self._account_number == other._account_number

    def __lt__(self, other: Account) -> bool:
        """Порівняння за балансом — для сортування списку рахунків."""
        if not isinstance(other, Account):
            return NotImplemented
        return self._balance < other._balance

    def __add__(self, other: Account) -> float:
        """Сума балансів двох рахунків."""
        if not isinstance(other, Account):
            return NotImplemented
        return self._balance + other._balance

    def __len__(self) -> int:
        """Кількість транзакцій по рахунку."""
        return len(self._transactions)


# ============================================================


class SavingsAccount(Account):
    """
    Ощадний рахунок.

    Не дозволяє знімати більше за поточний баланс.
    Нараховує відсотки на залишок (apply_interest).

    Attributes:
        _interest_rate: Річна відсоткова ставка (наприклад, 0.05 = 5%).
    """

    DEFAULT_INTEREST_RATE: float = 0.05  # 5% річних

    def __init__(
        self,
        owner: Owner,
        initial_balance: float = 0.0,
        interest_rate: float = DEFAULT_INTEREST_RATE,
    ) -> None:
        super().__init__(owner, initial_balance)

        if not isinstance(interest_rate, (int, float)):
            raise TypeError("Відсоткова ставка має бути числом.")
        if not (0 <= interest_rate <= 1):
            raise ValueError("Відсоткова ставка має бути від 0 до 1 (наприклад, 0.05).")

        self._interest_rate: float = float(interest_rate)

    # ---------- властивості ----------

    @property
    def interest_rate(self) -> float:
        return self._interest_rate

    # ---------- публічні методи ----------

    def withdraw(self, amount: float, description: str = "") -> Transaction:
        """
        Зняти кошти з ощадного рахунку.
        Забороняє знімати більше за поточний баланс.

        Raises:
            ValueError: Якщо суми недостатньо на рахунку.
        """
        self._check_active()
        if not isinstance(amount, (int, float)):
            raise TypeError("Сума має бути числом.")
        if amount <= 0:
            raise ValueError("Сума зняття має бути більше 0.")
        if amount > self._balance:
            raise ValueError(
                f"Недостатньо коштів. Баланс: {self._balance:.2f} грн, "
                f"запит: {amount:.2f} грн."
            )

        self._balance -= amount
        transaction = Transaction(
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            description=description or f"Зняття з рахунку {self._account_number}",
        )
        self._add_transaction(transaction)
        return transaction

    def apply_interest(self) -> Transaction:
        """
        Нарахувати відсотки на поточний залишок.
        Викликається вручну або автоматично раз на місяць.

        Returns:
            Transaction типу INTEREST.
        """
        self._check_active()
        interest_amount = round(self._balance * self._interest_rate, 2)
        if interest_amount <= 0:
            raise ValueError("Нарахування відсотків неможливе: баланс нульовий.")

        self._balance += interest_amount
        transaction = Transaction(
            amount=interest_amount,
            transaction_type=TransactionType.INTEREST,
            description=f"Нарахування {self._interest_rate * 100:.1f}% річних",
        )
        self._add_transaction(transaction)
        return transaction

    def get_statement(self) -> str:
        """Виписка по ощадному рахунку."""
        lines = [
            "=" * 60,
            f"  ВИПИСКА: Ощадний рахунок",
            f"  Номер:    {self._account_number}",
            f"  Власник:  {self._owner.full_name}",
            f"  Ставка:   {self._interest_rate * 100:.1f}% річних",
            f"  Баланс:   {self._balance:.2f} грн",
            f"  Статус:   {self._status.value}",
            "=" * 60,
        ]
        if self._transactions:
            lines.append("  Транзакції:")
            for t in sorted(self._transactions):
                lines.append(f"  {t}")
        else:
            lines.append("  Транзакцій немає.")
        lines.append("=" * 60)
        return "\n".join(lines)

    # ---------- магічні методи ----------

    def __str__(self) -> str:
        return (
            f"[Ощадний] {self._account_number} | "
            f"{self._owner.full_name} | "
            f"Баланс: {self._balance:.2f} грн | "
            f"Ставка: {self._interest_rate * 100:.1f}%"
        )


# ============================================================


class CreditAccount(Account):
    """
    Кредитний рахунок.

    Дозволяє балансу йти в мінус у межах кредитного ліміту.
    При від'ємному балансі нараховує комісію (apply_fee).

    Attributes:
        _credit_limit: Максимальна сума, на яку можна піти в мінус.
        _fee_rate: Щомісячна комісія на від'ємний залишок (наприклад, 0.02 = 2%).
    """

    DEFAULT_FEE_RATE: float = 0.02  # 2% на від'ємний залишок

    def __init__(
        self,
        owner: Owner,
        credit_limit: float,
        initial_balance: float = 0.0,
        fee_rate: float = DEFAULT_FEE_RATE,
    ) -> None:
        super().__init__(owner, initial_balance)

        if not isinstance(credit_limit, (int, float)):
            raise TypeError("Кредитний ліміт має бути числом.")
        if credit_limit <= 0:
            raise ValueError("Кредитний ліміт має бути більше 0.")
        if not isinstance(fee_rate, (int, float)):
            raise TypeError("Ставка комісії має бути числом.")
        if not (0 <= fee_rate <= 1):
            raise ValueError("Ставка комісії має бути від 0 до 1.")

        self._credit_limit: float = float(credit_limit)
        self._fee_rate: float = float(fee_rate)

    # ---------- властивості ----------

    @property
    def credit_limit(self) -> float:
        return self._credit_limit

    @property
    def fee_rate(self) -> float:
        return self._fee_rate

    @property
    def available_funds(self) -> float:
        """Доступна сума з урахуванням кредитного ліміту."""
        return self._balance + self._credit_limit

    # ---------- публічні методи ----------

    def withdraw(self, amount: float, description: str = "") -> Transaction:
        """
        Зняти кошти з кредитного рахунку.
        Дозволяє йти в мінус у межах кредитного ліміту.

        Raises:
            ValueError: Якщо перевищено кредитний ліміт.
        """
        self._check_active()
        if not isinstance(amount, (int, float)):
            raise TypeError("Сума має бути числом.")
        if amount <= 0:
            raise ValueError("Сума зняття має бути більше 0.")
        if amount > self.available_funds:
            raise ValueError(
                f"Перевищено кредитний ліміт. Доступно: {self.available_funds:.2f} грн, "
                f"запит: {amount:.2f} грн."
            )

        self._balance -= amount
        transaction = Transaction(
            amount=amount,
            transaction_type=TransactionType.WITHDRAWAL,
            description=description or f"Зняття з рахунку {self._account_number}",
        )
        self._add_transaction(transaction)
        return transaction

    def apply_fee(self) -> Optional[Transaction]:
        """
        Нарахувати комісію на від'ємний залишок.
        Якщо баланс >= 0 — комісія не нараховується.

        Returns:
            Transaction типу FEE або None якщо баланс невід'ємний.
        """
        self._check_active()
        if self._balance >= 0:
            return None

        fee_amount = round(abs(self._balance) * self._fee_rate, 2)
        if fee_amount <= 0:
            return None

        self._balance -= fee_amount
        transaction = Transaction(
            amount=fee_amount,
            transaction_type=TransactionType.FEE,
            description=f"Комісія {self._fee_rate * 100:.1f}% на від'ємний залишок",
        )
        self._add_transaction(transaction)
        return transaction

    def get_statement(self) -> str:
        """Виписка по кредитному рахунку."""
        lines = [
            "=" * 60,
            f"  ВИПИСКА: Кредитний рахунок",
            f"  Номер:    {self._account_number}",
            f"  Власник:  {self._owner.full_name}",
            f"  Ліміт:    {self._credit_limit:.2f} грн",
            f"  Баланс:   {self._balance:.2f} грн",
            f"  Доступно: {self.available_funds:.2f} грн",
            f"  Статус:   {self._status.value}",
            "=" * 60,
        ]
        if self._transactions:
            lines.append("  Транзакції:")
            for t in sorted(self._transactions):
                lines.append(f"  {t}")
        else:
            lines.append("  Транзакцій немає.")
        lines.append("=" * 60)
        return "\n".join(lines)

    # ---------- магічні методи ----------

    def __str__(self) -> str:
        return (
            f"[Кредитний] {self._account_number} | "
            f"{self._owner.full_name} | "
            f"Баланс: {self._balance:.2f} грн | "
            f"Ліміт: {self._credit_limit:.2f} грн"
        )


# ============================================================


class CurrencyAccount(SavingsAccount):
    """
    Валютний рахунок (успадковує SavingsAccount).

    Зберігає кошти у валюті та автоматично конвертує
    при поповненні/знятті через exchange_rate.

    Глибина наслідування: ABC -> Account -> SavingsAccount -> CurrencyAccount

    Attributes:
        _currency: Код валюти (наприклад, 'USD', 'EUR').
        _exchange_rate: Курс валюти до гривні (грн за 1 одиницю валюти).
    """

    SUPPORTED_CURRENCIES: tuple[str, ...] = ("USD", "EUR", "GBP", "PLN")

    def __init__(
        self,
        owner: Owner,
        currency: str,
        exchange_rate: float,
        initial_balance: float = 0.0,
        interest_rate: float = SavingsAccount.DEFAULT_INTEREST_RATE,
    ) -> None:
        super().__init__(owner, initial_balance, interest_rate)

        if not isinstance(currency, str):
            raise TypeError("Валюта має бути рядком.")
        currency = currency.upper()
        if currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(
                f"Непідтримувана валюта '{currency}'. "
                f"Доступні: {', '.join(self.SUPPORTED_CURRENCIES)}."
            )
        if not isinstance(exchange_rate, (int, float)):
            raise TypeError("Курс валюти має бути числом.")
        if exchange_rate <= 0:
            raise ValueError("Курс валюти має бути більше 0.")

        self._currency: str = currency
        self._exchange_rate: float = float(exchange_rate)

    # ---------- властивості ----------

    @property
    def currency(self) -> str:
        return self._currency

    @property
    def exchange_rate(self) -> float:
        return self._exchange_rate

    @exchange_rate.setter
    def exchange_rate(self, value: float) -> None:
        """Оновити курс валюти."""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("Курс валюти має бути додатнім числом.")
        self._exchange_rate = float(value)

    @property
    def balance_in_currency(self) -> float:
        """Баланс у валюті рахунку."""
        return round(self._balance / self._exchange_rate, 2)

    # ---------- публічні методи ----------

    def deposit_currency(self, amount_in_currency: float, description: str = "") -> Transaction:
        """
        Поповнити рахунок у валюті (конвертується в гривні автоматично).

        Args:
            amount_in_currency: Сума у валюті рахунку.
        """
        amount_uah = round(amount_in_currency * self._exchange_rate, 2)
        return self.deposit(
            amount_uah,
            description or f"Поповнення {amount_in_currency:.2f} {self._currency} "
                           f"за курсом {self._exchange_rate:.2f} грн/{self._currency}",
        )

    def withdraw_currency(self, amount_in_currency: float, description: str = "") -> Transaction:
        """
        Зняти кошти у валюті (конвертується з гривень автоматично).

        Args:
            amount_in_currency: Сума у валюті рахунку.
        """
        amount_uah = round(amount_in_currency * self._exchange_rate, 2)
        return self.withdraw(
            amount_uah,
            description or f"Зняття {amount_in_currency:.2f} {self._currency} "
                           f"за курсом {self._exchange_rate:.2f} грн/{self._currency}",
        )

    def get_statement(self) -> str:
        """Виписка по валютному рахунку."""
        lines = [
            "=" * 60,
            f"  ВИПИСКА: Валютний рахунок ({self._currency})",
            f"  Номер:    {self._account_number}",
            f"  Власник:  {self._owner.full_name}",
            f"  Валюта:   {self._currency}",
            f"  Курс:     {self._exchange_rate:.2f} грн/{self._currency}",
            f"  Баланс:   {self.balance_in_currency:.2f} {self._currency} "
            f"({self._balance:.2f} грн)",
            f"  Статус:   {self._status.value}",
            "=" * 60,
        ]
        if self._transactions:
            lines.append("  Транзакції:")
            for t in sorted(self._transactions):
                lines.append(f"  {t}")
        else:
            lines.append("  Транзакцій немає.")
        lines.append("=" * 60)
        return "\n".join(lines)

    # ---------- магічні методи ----------

    def __str__(self) -> str:
        return (
            f"[Валютний/{self._currency}] {self._account_number} | "
            f"{self._owner.full_name} | "
            f"Баланс: {self.balance_in_currency:.2f} {self._currency} "
            f"({self._balance:.2f} грн)"
        )