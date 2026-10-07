## Требования

- Python 3.8+
- PostgreSQL 12+ (или Docker)

## Установка и запуск

```bash
git clone https://github.com/ZuevaAlinam/zueva_alina_support
cd zueva_alina_support

python3 -m venv venv
source venv/bin/activate           # Linux / WSL
# venv\Scripts\activate            # Windows

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
# открыть .env и указать пароль от PostgreSQL

# Поднять базу (один из вариантов):
# A) локальный PostgreSQL:
sudo service postgresql start
sudo -u postgres psql -c "CREATE DATABASE zueva_alina;"
# B) через Docker:
docker compose up -d db

# Создать таблицы
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(bind=engine)"

# Наполнить малым объёмом (300 заявок)
python -m scripts.seed_small

# Или рабочим объёмом (50 000 заявок), займёт 5–15 минут
python -m scripts.seed_large

# Запустить
uvicorn app.main:app --host 0.0.0.0 --port 8000
