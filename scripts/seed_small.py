"""Малое наполнение: 50 пользователей, 5 категорий, 300 заявок, 900 комментариев."""
import random
from datetime import datetime, timedelta
from faker import Faker
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

    # Очистка (повторный запуск даёт тот же результат)
    db.query(models.Comment).delete()
    db.query(models.Ticket).delete()
    db.query(models.Category).delete()
    db.query(models.User).delete()
    db.commit()

    # Пользователи
    users = []
    for i in range(50):
        role = "support" if i < 10 else ("admin" if i == 10 else "user")
        u = models.User(
            username=f"user{i}",
            password_hash=auth.hash_password("demo"),
            role=role,
            full_name=fake.name(),
        )
        users.append(u)
        db.add(u)
    db.commit()

    # Категории
    categories = [
        models.Category(name="Техническая проблема", reaction_norm_hours=4),
        models.Category(name="Вопрос по оплате", reaction_norm_hours=8),
        models.Category(name="Жалоба", reaction_norm_hours=2),
        models.Category(name="Консультация", reaction_norm_hours=24),
        models.Category(name="Прочее", reaction_norm_hours=48),
    ]
    for c in categories:
        db.add(c)
    db.commit()

    # Заявки
    for _ in range(300):
        created = datetime.utcnow() - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        status = random.choice(["new", "in_progress", "closed"])
        t = models.Ticket(
            title=random.choice(TITLES),
            body=random.choice(BODIES),
            status=status,
            category_id=random.choice(categories).id,
            author_id=random.choice(users).id,
            created_at=created,
        )
        if status in ("in_progress", "closed"):
            t.assignee_id = random.choice(users[:11]).id
            t.first_response_at = created + timedelta(hours=random.randint(1, 30))
        if status == "closed":
            t.closed_at = created + timedelta(days=random.randint(1, 10))
        db.add(t)
    db.commit()

    # Комментарии
    tickets = db.query(models.Ticket).all()
    for _ in range(900):
        t = random.choice(tickets)
        author = random.choice(users)
        db.add(models.Comment(
            ticket_id=t.id,
            author_id=author.id,
            body=random.choice(COMMENTS),
            created_at=t.created_at + timedelta(hours=random.randint(1, 48)),
        ))
    db.commit()
    db.close()
    print("Small seed done: 50 users, 5 categories, 300 tickets, 900 comments")

if __name__ == "__main__":
    seed()