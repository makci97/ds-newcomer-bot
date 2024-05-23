FROM python:3.11
WORKDIR /app

# копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта в контейнер
COPY * .

# команда запуска приложения
CMD ["python", "app.py"]