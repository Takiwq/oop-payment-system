# ============================================
# Назва завдання: Платіжна система
# Опис: Unit-тести (unittest)
# ============================================

import unittest

from models import Owner, Transaction, TransactionType, TransactionStatus, AccountStatus
from accounts import Account, SavingsAccount, CreditAccount, CurrencyAccount
from payment_system import PaymentSystem


#  Допоміжна фабрика тестових даних

def make_owner(name: str = "Іван Франко", tax_id: str = "1234567890") -> Owner:
    return Owner(full_name=name, tax_id=tax_id)


def make_savings(owner: Owner = None, balance: float = 1000.0) -> SavingsAccount:
    return SavingsAccount(owner or make_owner(), initial_balance=balance)


def make_credit(owner: Owner = None, limit: float = 5000.0) -> CreditAccount:
    return CreditAccount(owner or make_owner(), credit_limit=limit)


def make_currency(owner: Owner = None) -> CurrencyAccount:
    return CurrencyAccount(owner or make_owner(), currency="USD", exchange_rate=41.0)


#  Тести класу Owner

class TestOwner(unittest.TestCase):

    def test_creation_valid(self):
        """Створення власника з коректними даними."""
        owner = Owner("Леся Українка", "9876543210", "+380501234567")
        self.assertEqual(owner.full_name, "Леся Українка")
        self.assertEqual(owner.tax_id, "9876543210")

    def test_invalid_name_empty(self):
        """Порожнє ім'я → ValueError."""
        with self.assertRaises(ValueError):
            Owner("", "1234567890")

    def test_invalid_tax_id_letters(self):
        """ІПН з літерами → ValueError."""
        with self.assertRaises(ValueError):
            Owner("Тест", "123456789A")

    def test_invalid_tax_id_short(self):
        """ІПН менше 10 цифр → ValueError."""
        with self.assertRaises(ValueError):
            Owner("Тест", "12345")

    def test_eq_same_tax_id(self):
        """Два власники з однаковим ІПН — рівні."""
        o1 = Owner("Іван Франко", "1234567890")
        o2 = Owner("І. Франко", "1234567890")
        self.assertEqual(o1, o2)

    def test_eq_different_tax_id(self):
        """Різні ІПН — не рівні."""
        o1 = make_owner()
        o2 = Owner("Інший", "0000000001")
        self.assertNotEqual(o1, o2)

    def test_add_remove_account(self):
        """Прив'язка та відв'язка номера рахунку."""
        owner = make_owner()
        owner.add_account("UA1234")
        self.assertIn("UA1234", owner.account_numbers)
        owner.remove_account("UA1234")
        self.assertNotIn("UA1234", owner.account_numbers)

    def test_str(self):
        owner = make_owner()
        self.assertIn("Іван Франко", str(owner))
        self.assertIn("1234567890", str(owner))

    def test_hash(self):
        """Власник може бути ключем словника."""
        owner = make_owner()
        d = {owner: "value"}
        self.assertEqual(d[owner], "value")


#  Тести класу Transaction

class TestTransaction(unittest.TestCase):

    def test_creation_valid(self):
        t = Transaction(100.0, TransactionType.DEPOSIT)
        self.assertEqual(t.amount, 100.0)
        self.assertEqual(t.status, TransactionStatus.COMPLETED)

    def test_invalid_amount_zero(self):
        with self.assertRaises(ValueError):
            Transaction(0, TransactionType.DEPOSIT)

    def test_invalid_amount_negative(self):
        with self.assertRaises(ValueError):
            Transaction(-50, TransactionType.DEPOSIT)

    def test_invalid_type(self):
        with self.assertRaises(TypeError):
            Transaction(100, "deposit")

    def test_str_contains_amount(self):
        t = Transaction(250.0, TransactionType.WITHDRAWAL)
        self.assertIn("250.00", str(t))

    def test_lt_ordering(self):
        """Транзакції сортуються за датою (обидві створені одразу — рівні або lt=False)."""
        t1 = Transaction(100, TransactionType.DEPOSIT)
        t2 = Transaction(200, TransactionType.DEPOSIT)
        # t1 створено раніше → t1 < t2 або t1 == t2 (мілісекунди)
        self.assertFalse(t2 < t1)

    def test_status_setter_valid(self):
        t = Transaction(100, TransactionType.DEPOSIT)
        t.status = TransactionStatus.FAILED
        self.assertEqual(t.status, TransactionStatus.FAILED)

    def test_status_setter_invalid(self):
        t = Transaction(100, TransactionType.DEPOSIT)
        with self.assertRaises(TypeError):
            t.status = "failed"


#  Тести SavingsAccount

class TestSavingsAccount(unittest.TestCase):

    def setUp(self):
        self.owner = make_owner()
        self.acc = SavingsAccount(self.owner, initial_balance=1000.0)

    def test_creation(self):
        self.assertEqual(self.acc.balance, 1000.0)
        self.assertEqual(self.acc.status, AccountStatus.ACTIVE)

    def test_deposit(self):
        self.acc.deposit(500.0)
        self.assertAlmostEqual(self.acc.balance, 1500.0)

    def test_withdraw_valid(self):
        self.acc.withdraw(300.0)
        self.assertAlmostEqual(self.acc.balance, 700.0)

    def test_withdraw_exceeds_balance(self):
        """Зняття більше балансу → ValueError."""
        with self.assertRaises(ValueError):
            self.acc.withdraw(9999.0)

    def test_withdraw_zero(self):
        with self.assertRaises(ValueError):
            self.acc.withdraw(0)

    def test_apply_interest(self):
        self.acc.apply_interest()
        self.assertAlmostEqual(self.acc.balance, 1050.0)  # 5% від 1000

    def test_apply_interest_zero_balance(self):
        acc = SavingsAccount(Owner("Тест", "1111111111"), initial_balance=0.0)
        with self.assertRaises(ValueError):
            acc.apply_interest()

    def test_block_and_unblock(self):
        self.acc.block()
        self.assertEqual(self.acc.status, AccountStatus.BLOCKED)
        with self.assertRaises(ValueError):
            self.acc.deposit(100)
        self.acc.unblock()
        self.assertEqual(self.acc.status, AccountStatus.ACTIVE)

    def test_len_transactions(self):
        self.acc.deposit(100)
        self.acc.withdraw(50)
        self.assertEqual(len(self.acc), 2)

    def test_add_magic(self):
        other = make_savings(balance=500.0)
        total = self.acc + other
        self.assertAlmostEqual(total, 1500.0)

    def test_lt_magic(self):
        rich = make_savings(balance=9000.0)
        self.assertLess(self.acc, rich)

    def test_invalid_owner_type(self):
        with self.assertRaises(TypeError):
            SavingsAccount("не власник")

    def test_invalid_initial_balance(self):
        with self.assertRaises(ValueError):
            SavingsAccount(self.owner, initial_balance=-100)

    def test_get_statement_contains_number(self):
        stmt = self.acc.get_statement()
        self.assertIn(self.acc.account_number, stmt)

    def test_owner_linked(self):
        """Рахунок автоматично прив'язується до власника."""
        self.assertIn(self.acc.account_number, self.owner.account_numbers)


#  Тести CreditAccount

class TestCreditAccount(unittest.TestCase):

    def setUp(self):
        self.owner = Owner("Марко Вовчок", "2222222222")
        self.acc = CreditAccount(self.owner, credit_limit=5000.0, initial_balance=0.0)

    def test_withdraw_within_limit(self):
        self.acc.withdraw(3000.0)
        self.assertAlmostEqual(self.acc.balance, -3000.0)

    def test_withdraw_exceeds_limit(self):
        with self.assertRaises(ValueError):
            self.acc.withdraw(6000.0)

    def test_available_funds(self):
        self.assertAlmostEqual(self.acc.available_funds, 5000.0)
        self.acc.withdraw(2000)
        self.assertAlmostEqual(self.acc.available_funds, 3000.0)

    def test_apply_fee(self):
        self.acc.withdraw(1000.0)   # баланс = -1000
        fee_tx = self.acc.apply_fee()
        self.assertIsNotNone(fee_tx)
        # комісія 2% від 1000 = 20 грн
        self.assertAlmostEqual(fee_tx.amount, 20.0)

    def test_apply_fee_positive_balance(self):
        """Комісія не нараховується при невід'ємному балансі."""
        self.acc.deposit(100)
        result = self.acc.apply_fee()
        self.assertIsNone(result)

    def test_invalid_credit_limit(self):
        with self.assertRaises(ValueError):
            CreditAccount(self.owner, credit_limit=-1000)

    def test_str(self):
        self.assertIn("Кредитний", str(self.acc))
        self.assertIn("5000.00", str(self.acc))


#  Тести CurrencyAccount

class TestCurrencyAccount(unittest.TestCase):

    def setUp(self):
        self.owner = Owner("Тарас Шевченко", "3333333333")
        self.acc = CurrencyAccount(
            self.owner, currency="USD", exchange_rate=41.0, initial_balance=0.0
        )

    def test_deposit_currency(self):
        self.acc.deposit_currency(100.0)   # 100 USD × 41 = 4100 грн
        self.assertAlmostEqual(self.acc.balance, 4100.0)
        self.assertAlmostEqual(self.acc.balance_in_currency, 100.0)

    def test_withdraw_currency(self):
        self.acc.deposit_currency(200.0)
        self.acc.withdraw_currency(50.0)   # залишок 150 USD
        self.assertAlmostEqual(self.acc.balance_in_currency, 150.0)

    def test_unsupported_currency(self):
        with self.assertRaises(ValueError):
            CurrencyAccount(self.owner, currency="BTC", exchange_rate=1_000_000)

    def test_invalid_exchange_rate(self):
        with self.assertRaises(ValueError):
            CurrencyAccount(self.owner, currency="USD", exchange_rate=-1)

    def test_exchange_rate_setter(self):
        self.acc.exchange_rate = 42.5
        self.assertAlmostEqual(self.acc.exchange_rate, 42.5)

    def test_inheritance(self):
        """CurrencyAccount успадковує SavingsAccount і Account."""
        self.assertIsInstance(self.acc, SavingsAccount)
        self.assertIsInstance(self.acc, Account)

    def test_str_contains_currency(self):
        self.assertIn("USD", str(self.acc))


#  Тести PaymentSystem

class TestPaymentSystem(unittest.TestCase):

    def setUp(self):
        self.system = PaymentSystem("МійБанк")
        self.owner1 = Owner("Іван Франко", "1234567890")
        self.owner2 = Owner("Леся Українка", "0987654321")
        self.acc1 = SavingsAccount(self.owner1, initial_balance=2000.0)
        self.acc2 = SavingsAccount(self.owner2, initial_balance=500.0)
        self.system.register(self.acc1)
        self.system.register(self.acc2)

    def test_len(self):
        self.assertEqual(len(self.system), 2)

    def test_getitem(self):
        fetched = self.system[self.acc1.account_number]
        self.assertEqual(fetched, self.acc1)

    def test_getitem_missing(self):
        with self.assertRaises(KeyError):
            _ = self.system["UA0000000000000000"]

    def test_contains(self):
        self.assertIn(self.acc1.account_number, self.system)

    def test_register_duplicate(self):
        with self.assertRaises(ValueError):
            self.system.register(self.acc1)

    def test_transfer(self):
        self.system.transfer(self.acc1, self.acc2, 300.0)
        self.assertAlmostEqual(self.acc1.balance, 1700.0)
        self.assertAlmostEqual(self.acc2.balance, 800.0)

    def test_transfer_same_account(self):
        with self.assertRaises(ValueError):
            self.system.transfer(self.acc1, self.acc1, 100.0)

    def test_transfer_insufficient_funds(self):
        with self.assertRaises(ValueError):
            self.system.transfer(self.acc2, self.acc1, 9999.0)

    def test_transfer_unregistered(self):
        stranger = make_savings(balance=100.0)
        with self.assertRaises(ValueError):
            self.system.transfer(self.acc1, stranger, 50.0)

    def test_get_total_assets(self):
        self.assertAlmostEqual(self.system.get_total_assets(), 2500.0)

    def test_find_by_owner_tax_id(self):
        results = self.system.find_by_owner_tax_id("1234567890")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.acc1)

    def test_str(self):
        self.assertIn("МійБанк", str(self.system))
        self.assertIn("2", str(self.system))

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            PaymentSystem("")


if __name__ == "__main__":
    unittest.main(verbosity=2)