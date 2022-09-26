import random


def generate_username(first_name, last_name):
    return f"{first_name}{last_name}{random.randint(100, 999)}".lower().replace(" ", "")


def password_generator(size=10):
    capital = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    small = "abcdefghijklmnopqrstuvwxyz"
    numbers = "1234567890"
    special_characters = "!@#$%^&*"
    chars = capital + numbers + special_characters + small

    return ''.join(random.choice(chars) for _ in range(size))