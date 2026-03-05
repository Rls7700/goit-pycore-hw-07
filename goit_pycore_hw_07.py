from __future__ import annotations

from collections import UserDict
from datetime import datetime, date, timedelta
from typing import Callable

class Field:
    """Базовий клас для полів запису."""

    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)
    
    
class Name(Field):
    """Клас для зберігання імені контакту."""
    pass


class Phone(Field):
    """Клас для зберігання номеру телефону. Валідація формату 10 цифр."""

    def __init__(self, value: str):
        self._validate(value)
        super().__init__(value)

    @staticmethod
    def _validate(value: str) -> None:
        if not(isinstance(value, str) and value.isdigit() and len(value) == 10):
            raise ValueError ("Phone number must contain exactly 10 digits.")
        

class Birthday(Field):
    """Клас для зберігання дня народження."""

    def __init__(self, value: str):
        try:
            bday_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(bday_date)

    def __str__(self) -> str:
        return self.value.strftime("%d.%m.%Y")
    

class Record:
    """Клас для зберігання інформації про контакт з іменем та смписком телефонів."""

    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str) -> None:
        """Додавання нового телефонного номеру."""
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        """Видалення телефонного номеру."""
        phone_obj = self.find_phone(phone)
        if phone_obj is None:
            raise ValueError ("Phone number not found.")
        self.phones.remove(phone_obj)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """Замінює старий номер телефону на новий."""
        phone_obj = self.find_phone(old_phone)
        if phone_obj is None:
            raise ValueError("Old phone number not found.")
        phone_obj.value = Phone(new_phone).value 

    def find_phone(self, phone: str) -> Phone | None:
        """Шукає обєкт телефону за його значенням."""
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj
        return None
    
    def add_birthday(self, birthday:str) -> None:
        """Додає/оновлює день народження контакту."""
        self.birthday = Birthday(birthday)
    
    def __str__(self) -> str:
        phones_str = "; " .join(p.value for p in self.phones) if self.phones else "-"
        bday_str = str(self.birthday) if self.birthday else "-"
        return f"Name: {self.name.value}, phones: {phones_str}, birthday: {bday_str}"
    

class AddressBook(UserDict):
    """Класс для зберігання записів та керування ними."""

    def add_record(self, record: Record) -> None:
        """Додає запис до адресної книги."""
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        """Знаходить запис за імям."""
        return self.data.get(name)
    
    def delete(self, name: str) -> None:
        """Видаляє запис за імям."""
        if name not in self.data:
            raise KeyError("Contact not found.")
        del self.data[name]

    def get_upcoming_birthdays(self, days: int = 7) -> list[dict]:
        """Повертає список контактів, яких треба привітати в найближчі 7 днів"""
        today = date.today()
        end_date = today + timedelta(days=days)
        result: list[dict] =[]

        for record in self.data.values():
            if record.birthday is None:
                continue

            bday: date = record.birthday.value
            # в поточному році
            try:
                bday_this_year = date(today.year, bday.month, bday.day)
            except ValueError:
                # якщо 29.02 рік не вискоксний, беремо 28.02
                bday_this_year = date(today.year, 2,28)

            # якщо вже минув у цьому році - беремо наступний рік
            if bday_this_year < today:
                next_year = today.year + 1
                try:
                    bday_this_year = date(today.year +1, bday.month, bday.day)
                except ValueError:
                    bday_this_year = date(next_year, 2,28)

            # якщо входить у вікно найближчих днів
            if today <= bday_this_year <= end_date:
                congrats_date = bday_this_year

                # 5 = Saturday, 6 = Sunday
                if congrats_date.weekday() == 5:
                    congrats_date += timedelta(days=2)
                elif congrats_date.weekday() == 6:
                    congrats_date += timedelta(days=1)

                result.append(
                    {
                        "name": record.name.value,
                        "congratulation_date": congrats_date.isoformat(),
                    }
                )

        result.sort(key=lambda x: x["congratulation_date"])
        return result

# DECORATOR + PARSER

def input_error(func: Callable):
    """Декоратор для обробки типових помилок вводу."""
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Not enough arguments for this command."
        except KeyError as e:
            return str(e).strip("'")
        except ValueError as e:
            return str(e)
    return inner

def parse_input(user_input: str) -> tuple[str, list[str]]:
    user_input = user_input.strip()
    parts = user_input.split()

    if not parts:
        return "", []
    
    command = parts[0].lower()
    args = parts[1:]

    return command, args

# HANDLERS

@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    name, phone, *_ = args

    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        record.add_phone(phone)
        return "Contact added."
    
    # якщо контакт існує, додаємо ще один номер
    record.add_phone(phone)
    return "Contact updated."

@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    name, old_phone, new_phone, *_ = args

    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    
    record.edit_phone(old_phone, new_phone)
    return "Phone changed."

@input_error
def phone_contact(args: list[str], book: AddressBook) -> str:
    name, *_ = args

    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    
    if not record.phones:
        return "No phone numbers."
    
    phones_str = ";" .join(p.value for p in record.phones)
    return f"{record.name.value}: {phones_str}"

@input_error
def all_contacts(args: list[str], book: AddressBook) -> str:
    if not book.data:
        return "Address book is empty."
    return "\n" .join(str(record) for record in book.data.values())

@input_error
def add_birthday(args: list[str], book: AddressBook) -> str:
    name, bday, *_ = args

    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    record.add_birthday(bday)
    return "Birthday added."

@input_error
def show_birthday(args: list[str], book: AddressBook) -> str:
    name, *_ = args

    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    
    if record.birthday is None:
        return "Birthday is not set."
    
    return f"{record.name.value}: {record.birthday}"

@input_error
def birthdays(args: list[str], book: AddressBook) -> str:
    upcoming = book.get_upcoming_birthdays(days=7)
    if not upcoming:
        return "No birthdays in the next 7 days."
    
    lines = ["Upcoming birthdays (next 7 days):"]
    for item in upcoming:
        lines.append(f"{item['name']} -> {item['congratulation_date']}")
    return "\n" .join(lines)


# MAIN

def main() -> None:
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(phone_contact(args, book))

        elif command == "all":
            print(all_contacts(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


    
if __name__ == "__main__":
    main()

    # # Створення нової адресної книги
    # book = AddressBook()

    # # Створення запису для John
    # john_record = Record("John")
    # john_record.add_phone("1234567890")
    # john_record.add_phone("5555555555")

    # # Додавання запису John до адресної книги
    # book.add_record(john_record)

    # # Створення та додавання нового запису для Jane
    # jane_record = Record("Jane")
    # jane_record.add_phone("9876543210")
    # book.add_record(jane_record)

    # # Створення запису для Test
    # # test_record = Record("Test")
    # # test_record.add_phone("00112233")
    # # book.add_record(test_record)

    # # Виведення всіх записів 
    # for _, record in book.data.items():
    #     print(record)

    # # Знаходження та редагування телефону для John
    # john = book.find("John")
    # if john:
    #     john.edit_phone("1234567890", "1112223333")
    #     print(john)

    #     # Пошук конкртеного телефону в записі John
    #     found_phone = john.find_phone("5555555555")
    #     print(f"{john.name}: {found_phone}") #5555555555

    # # Видалення запису Jane
    # book.delete("Jane")