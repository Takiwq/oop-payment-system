# ============================================
# Назва завдання: Платіжна система
# Студент: Страшненко Дмитро 
# Додатковий функціонал: валютні рахунки (CurrencyAccount),
#   блокування/розблокування рахунку, автонарахування відсотків і комісій
# ============================================

from models import Owner, TransactionType, AccountStatus
from accounts import SavingsAccount, CreditAccount, CurrencyAccount
from payment_system import PaymentSystem


def separator(title: str = "") -> None:
    """Виводить роздільник секцій для зручного читання."""
    line = "=" * 60
    if title:
        print(f"\n{line}")
        print(f"  {title}")
        print(line)
    else:
        print(line)



#  1. Створення власників

separator("1. Створення власників (Owner)")

ivan = Owner(full_name="Іван Франко", tax_id="1234567890", phone="+380501112233")
lesya = Owner(full_name="Леся Українка", tax_id="0987654321", phone="+380672223344")
taras = Owner(full_name="Тарас Шевченко", tax_id="3333333333")

print(ivan)
print(lesya)
print(repr(taras))

# Перевірка рівності власників (за ІПН)
ivan_copy = Owner("І. Франко", "1234567890")
print(f"\nіван == ivan_copy (однаковий ІПН): {ivan == ivan_copy}")
print(f"ivan == lesya (різний ІПН):         {ivan == lesya}")


#  2. Створення рахунків

separator("2. Створення рахунків")

savings_ivan  = SavingsAccount(ivan,  initial_balance=5000.0)
savings_lesya = SavingsAccount(lesya, initial_balance=1200.0, interest_rate=0.07)
credit_ivan   = CreditAccount(ivan,   credit_limit=10_000.0, initial_balance=0.0)
usd_taras     = CurrencyAccount(taras, currency="USD", exchange_rate=41.0, initial_balance=0.0)

print(savings_ivan)
print(savings_lesya)
print(credit_ivan)
print(usd_taras)

# Рахунки автоматично прив'язалися до власника
print(f"\nРахунки Івана: {ivan.account_numbers}")


#  3. Реєстрація в платіжній системі

separator("3. Реєстрація у платіжній системі")

bank = PaymentSystem("ТестБАНК")
bank.register(savings_ivan)
bank.register(savings_lesya)
bank.register(credit_ivan)
bank.register(usd_taras)

print(bank)
print(f"Кількість рахунків (__len__): {len(bank)}")
print(f"Рахунок Івана через __getitem__: {bank[savings_ivan.account_number]}")



#  4. Операції з ощадним рахунком

separator("4. Операції з ощадним рахунком (SavingsAccount)")

savings_ivan.deposit(2000.0, description="Зарплата за квітень")
savings_ivan.withdraw(500.0, description="Оплата комунальних послуг")
savings_ivan.apply_interest()   # нарахування 5% річних

print(f"Баланс Івана після операцій: {savings_ivan.balance:.2f} грн")
print(f"Кількість транзакцій (__len__): {len(savings_ivan)}")

# Виписка
print("\n" + savings_ivan.get_statement())

# Спроба зняти більше за баланс
print("\n-- Спроба зняти більше за баланс --")
try:
    savings_ivan.withdraw(999_999.0)
except ValueError as e:
    print(f"ValueError: {e}")


#  5. Операції з кредитним рахунком

separator("5. Операції з кредитним рахунком (CreditAccount)")

credit_ivan.withdraw(7000.0, description="Купівля техніки")
print(f"Баланс після зняття 7000 грн: {credit_ivan.balance:.2f} грн")
print(f"Доступно ще:                  {credit_ivan.available_funds:.2f} грн")

fee_tx = credit_ivan.apply_fee()   # комісія 2% від abs(-7000) = 140 грн
if fee_tx:
    print(f"Нарахована комісія: {fee_tx.amount:.2f} грн")

print("\n" + credit_ivan.get_statement())

# Спроба перевищити кредитний ліміт
print("\n-- Спроба перевищити кредитний ліміт --")
try:
    credit_ivan.withdraw(50_000.0)
except ValueError as e:
    print(f"ValueError: {e}")


#  6. Валютний рахунок

separator("6. Валютний рахунок (CurrencyAccount)")

usd_taras.deposit_currency(500.0)    # 500 USD × 41 = 20 500 грн
usd_taras.withdraw_currency(100.0)   # -100 USD → залишок 400 USD
usd_taras.apply_interest()           # 5% на залишок у гривнях

print(f"Баланс у USD: {usd_taras.balance_in_currency:.2f} {usd_taras.currency}")
print(f"Баланс у грн: {usd_taras.balance:.2f} грн")

# Оновлення курсу
usd_taras.exchange_rate = 42.5
print(f"Новий курс:   {usd_taras.exchange_rate} грн/USD")

print("\n" + usd_taras.get_statement())

# Спроба непідтримуваної валюти
print("\n-- Спроба створити рахунок у BTC --")
try:
    CurrencyAccount(taras, currency="BTC", exchange_rate=3_000_000)
except ValueError as e:
    print(f"ValueError: {e}")


#  7. Переказ між рахунками

separator("7. Переказ між рахунками (transfer)")

print(f"До переказу — Іван:  {savings_ivan.balance:.2f} грн")
print(f"До переказу — Леся:  {savings_lesya.balance:.2f} грн")

bank.transfer(savings_ivan, savings_lesya, 1000.0, description="Повернення боргу")

print(f"Після переказу — Іван:  {savings_ivan.balance:.2f} грн")
print(f"Після переказу — Леся:  {savings_lesya.balance:.2f} грн")

# Переказ на себе — помилка
print("\n-- Переказ на той самий рахунок --")
try:
    bank.transfer(savings_ivan, savings_ivan, 100.0)
except ValueError as e:
    print(f"ValueError: {e}")

# Переказ незареєстрованого рахунку
print("\n-- Переказ незареєстрованого рахунку --")
stranger = SavingsAccount(Owner("Чужий", "5555555555"), initial_balance=100.0)
try:
    bank.transfer(savings_ivan, stranger, 50.0)
except ValueError as e:
    print(f"ValueError: {e}")


#  8. Блокування рахунку

separator("8. Блокування / розблокування рахунку")

savings_lesya.block()
print(f"Статус Лесі: {savings_lesya.status.value}")

print("\n-- Спроба поповнити заблокований рахунок --")
try:
    savings_lesya.deposit(100.0)
except ValueError as e:
    print(f"ValueError: {e}")

savings_lesya.unblock()
print(f"Статус після розблокування: {savings_lesya.status.value}")
savings_lesya.deposit(300.0, description="Поповнення після розблокування")
print(f"Баланс Лесі: {savings_lesya.balance:.2f} грн")


#  9. Магічні методи

separator("9. Демонстрація магічних методів")

# __add__ — об'єднання балансів
total = savings_ivan + savings_lesya
print(f"savings_ivan + savings_lesya = {total:.2f} грн")

# __lt__ — порівняння за балансом
print(f"savings_ivan < savings_lesya: {savings_ivan < savings_lesya}")
print(f"savings_lesya < savings_ivan: {savings_lesya < savings_ivan}")

# __eq__ для рахунків
print(f"savings_ivan == savings_ivan: {savings_ivan == savings_ivan}")
print(f"savings_ivan == savings_lesya: {savings_ivan == savings_lesya}")

# __contains__ для системи
print(f"'{savings_ivan.account_number}' in bank: {savings_ivan.account_number in bank}")
print(f"'UA0000000000000000' in bank: {'UA0000000000000000' in bank}")

# repr
print(f"\nrepr(savings_ivan): {repr(savings_ivan)}")
print(f"repr(bank):         {repr(bank)}")


#  10. Аналітика системи

separator("10. Аналітика платіжної системи")

print(bank.get_summary())

# Пошук за ІПН
results = bank.find_by_owner_tax_id(ivan.tax_id)
print(f"\nРахунки Івана (знайдено {len(results)}):")
for acc in results:
    print(f"  {acc}")

print(f"\nЗагальні активи: {bank.get_total_assets():.2f} грн")


#  11. Валідація (TypeError / ValueError)

separator("11. Демонстрація валідації")

print("-- Невірний ІПН --")
try:
    Owner("Тест", "12345")
except ValueError as e:
    print(f"ValueError: {e}")

print("-- Від'ємний баланс при створенні --")
try:
    SavingsAccount(ivan, initial_balance=-500)
except ValueError as e:
    print(f"ValueError: {e}")

print("-- Власник не є об'єктом Owner --")
try:
    SavingsAccount("не власник")  # type: ignore
except TypeError as e:
    print(f"TypeError: {e}")

print("-- Від'ємний кредитний ліміт --")
try:
    CreditAccount(ivan, credit_limit=-1000)
except ValueError as e:
    print(f"ValueError: {e}")

print("-- Транзакція з нульовою сумою --")
try:
    from models import Transaction, TransactionType
    Transaction(0, TransactionType.DEPOSIT)
except ValueError as e:
    print(f"ValueError: {e}")

separator("Демонстрацію завершено")