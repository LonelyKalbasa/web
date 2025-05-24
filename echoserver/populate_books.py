import os
import django
from faker import Faker
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore_project.settings')
django.setup()

from bookstore.models import Book

fake = Faker('ru_RU')

def create_books(num=10):
    for _ in range(num):
        Book.objects.create(
            title=fake.catch_phrase(),
            author=fake.name(),
            price=fake.random_number(digits=3),
            description=fake.text(),
            published_date=fake.date_between(start_date='-10y', end_date='today')
        )

if __name__ == '__main__':
    print("Создание тестовых книг...")
    create_books(15)
    print("Готово!")