"""Рабочее наполнение: 3000 пользователей, 10 категорий, 50000–100000 заявок, 150000–300000 комментариев."""
import random
from datetime import datetime, timedelta
from faker import Faker
from faker.contrib.pytest.plugin import faker
from faker.proxy import Faker

from app.database import SessionLocal, Base, engine
from app import models, auth
fake = Faker("ru_RU")
TITLES = [
    "Не работает вход в личный кабинет",
    "Ошибка при оплате картой",
    "Не приходит письмо с подтверждением",
    "Зависает приложение при загрузке",
    "Не могу восстановить пароль",
    "Ошибка 500 на странице заказа",
    "Медленно работает поиск",
    "Пропали данные из профиля",
    "Двойное списание средств",
    "Не открывается вложение в заявке",
]

BODIES = [
    "Пытаюсь зайти с утра, ввожу корректный пароль, но система пишет «неверные данные».",
    "При оплате заказа карта списалась дважды, деньги не вернулись.",
    "Письмо с кодом подтверждения не приходит уже 30 минут, спам проверял.",
    "Приложение открывается, но на экране загрузки висит бесконечно.",
    "Кнопка «восстановить пароль» ничего не делает, письмо не приходит.",
    "На странице оформления заказа выдаёт 500-ю ошибку.",
    "Поиск по каталогу отвечает больше 10 секунд.",
    "После смены пароля пропали сохранённые адреса.",
    "С карты списалось 2 раза по 1500 рублей за один заказ.",
    "В заявке не открывается приложенный PDF, браузер пишет «файл повреждён».",
]
COMMENTS = [
    "Спасибо, проблема воспроизвелась, разбираемся.",
    "Уточните, пожалуйста, версию браузера и операционной системы.",
    "Пришлите скриншот ошибки, так будет быстрее.",
    "Проверил у себя — воспроизводится, передал разработчикам.",
    "Попробуйте очистить кэш браузера и повторить попытку.",
    "Проблема на стороне платёжного шлюза, ждём ответа от партнёра.",
    "Дублирую обращение в профильный отдел, ответ будет в течение часа.",
    "Приношу извинения за доставленные неудобства, исправим в ближайшем релизе.",
    "Письмо могло попасть в спам, проверьте папку «Спам» и «Промоакции».",
    "Восстановление пароля работает через почту, проверьте ссылку в письме.",
    "Заявка принята в работу, ориентировочный срок — 2 рабочих дня.",
    "Данные восстановлены, проверьте, пожалуйста, личный кабинет.",
    "Ошибка 500 возникала из-за обновления, сейчас всё должно работать.",
    "Платёж вернулся, проверьте баланс карты, обычно занимает до 5 дней.",
    "Поиск оптимизировали, теперь должен отвечать быстрее.",
    "Адреса вернули, приносим извинения за временные неудобства.",
    "Возврат оформлен, ожидайте зачисления в течение 3–5 рабочих дней.",
    "Файл перезалили, попробуйте открыть вложение заново.",
    "Передал вашу заявку старшему специалисту, он свяжется с вами.",
    "Проблема с приложением исправлена в версии 2.4.1, обновите, пожалуйста.",
    "Уточните, пожалуйста, номер заказа и последние 4 цифры карты.",
    "Ваш вопрос решён, закрываю заявку. Если что-то ещё — пишите.",
    "Нашли причину: конфликт с расширением браузера. Отключите его и проверьте.",
    "Подтверждаю, проблема массовая, работаем над устранением.",
    "Спасибо за подробное описание, это сильно помогло.",
]
random.seed(42)

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    db.query(models.Comment).delete()
    db.query(models.Ticket).delete()
    db.query(models.Category).delete()
    db.query(models.User).delete()
    db.commit()

    # Пользователи
    users = []
    for i in range(3000):
        role = "support" if i < 100 else ("admin" if i == 100 else "user")
        u = models.User(
            username=f"user{i}",
            password_hash=auth.hash_password("demo"),
            role=role,
            full_name=fake.name(),
        )
        users.append(u)
        if i % 500 == 0:
            db.add(u)
    for u in users:
        db.add(u)
    db.commit()

    # Категории
    categories = [models.Category(name=f"Категория {i}", reaction_norm_hours=random.choice([2,4,8,24,48])) for i in range(10)]
    for c in categories:
        db.add(c)
    db.commit()

    # Заявки — 50 000
    statuses = ["new", "in_progress", "closed"]
    for batch in range(50):
        for _ in range(1000):
            created = datetime.utcnow() - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
            status = random.choice(statuses)
            t = models.Ticket(
                title=random.choice(TITLES),
                body=random.choice(BODIES),
                status=status,
                category_id=random.choice(categories).id,
                author_id=random.choice(users).id,
                created_at=created,
            )
            if status in ("in_progress", "closed"):
                t.assignee_id = random.choice(users[:100]).id
                t.first_response_at = created + timedelta(hours=random.randint(1, 60))
            if status == "closed":
                t.closed_at = created + timedelta(days=random.randint(1, 30))
            db.add(t)
        db.commit()
        print(f"Tickets batch {batch+1}/50 done")

    # Комментарии — 200 000
    ticket_ids = [row[0] for row in db.query(models.Ticket.id).all()]
    for batch in range(200):
        for _ in range(1000):
            t_id = random.choice(ticket_ids)
            db.add(models.Comment(
                ticket_id=t_id,
                author_id=random.choice(users).id,
                body=random.choice(COMMENTS),
            ))
        db.commit()
        print(f"Comments batch {batch+1}/200 done")

    db.close()
    print("Large seed done: 3000 users, 10 categories, 50000 tickets, 200000 comments")

if __name__ == "__main__":
    seed()