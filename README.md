# Инструкция по использованию бота

## 1. Запуск бота

Бот доступен в TG [Pimp my DS](https://t.me/pimp_my_ds_bot)

Чтобы запустить бота, нажмите кнопку "Меню" или выберите команду `/start`.


## 2. Выбор сценария использования

После запуска бот предложит вам выбрать один из трех сценариев использования:

- Прокачка знаний
- Помощь в решении задач
- Объяснение IT-мемов

В зависимости от сценария использования, бот поддерживает работу с типами данных: текст, картинки, аудио.

## 3. Завершение диалога

Чтобы завершить диалог и вернуться в меню для выбора другой задачи, используйте кнопки "BACK", `/finish_dialog`, "Отмена" или начните новый диалог через команду `/start`.

## 4. Сценарии использования

### 4.1. Сценарий "Прокачка знаний"

В этом сценарии можно взаимодействовать с ботом  **как в текстовом, так и в аудиоформате**.

1. Для правильного подбора заданий в "Настройках пользователя" установите свой уровень подготовки и требуемую сложность заданий, После настройки нажмите кнопку "BACK" для возврата в меню выбора заданий.

1. При выборе одного из возможных вариантов использования (см. ниже), бот попросит выбрать тему.

1. Какие задания выполняет бот?
   - Подготовка к собеседованию:

      Бот сформулирует две задачи на алгоритмы с учетом выбранного уровня сложности (опишет условия, укажет примеры данных на вход и ожидаемый вывод) и задаст серию вопросов по DS/ML.

   - Задача по алгоритмам:

      Бот сформулирует задачу на алгоритмы (опишет условия, примеры данных на вход и ожидаемый вывод) и задаст по ней вопросы (память и время выполнения) на заданную пользователем тему с настроенным уровнем сложности.

   - Задача по ML:

      Бот сформулирует ML-задачу по теории на заданную пользователем тему указанного уровня сложности.

   - Создай тест:

      Бот предоставит тест с вариантами ответов, который поможет пользователю оценить свои знания и умения по заданной теме.

   - ROADMAP:

      Бот предоставит план с пунктами, которые помогут пользователю освоить выбранную тему.

   - Психологическая помощь:

      Опытный психолог в режиме чат-бота поможет DS-разработчику подготовиться к собеседованию.

1. Чтобы завершить диалог и вернуться в меню для выбора другой задачи, используйте команду `/finish_dialog`. Эта кнопка может быть видна отдельно внизу или представлена в виде иконки рядом со смайлами.

### 4.2. Сценарий "Помощь в решении задач"

1. Если пользователь передумал и хочет выбрать основной сценарий использования, нажмите кнопку "Назад" для возврата в меню выбора сценариев.  

1. В этом сценарии, пользователь может загрузить в бот следующие элементы для решения задачи:
   - Описание задачи  
   - Код  
   - Датасет  

1. Если пользователь просит описать задачу:

   а) Бот сформулирует пошаговую инструкцию для выполнения задачи, основываясь на краткой информации, предоставленной пользователем.

   ИЛИ

   б) По краткому описанию задачи бот предложит код для ее решения.

1. В случае, если пользователь уже написал код для решения задачи, бот проанализирует и оптимизирует его, предлагая возможные улучшения.

   Что можно сделать с загружаемым кодом?

   - Объяснить:

      Бот предоставит словесное описание того, что происходит в коде в целом и построчно.

   - Пофиксить:

      Бот проверяет код на наличие багов и отвечает, что либо их нет, либо переписывает решение, исправляя ошибки.

   - Отрефакторить:

      Бот предлагает изменения в коде, подсвечивает проблемы и указывает на необходимость оптимизации.

   - Отревьюировать:

      Бот проводит анализ кода на предмет ошибок, подсвечивает проблемы с эффективностью и оптимальностью использования.

1. Рассмотрим подробнее сценарий с загрузкой датасета:  

   - Здесь мы ожидаем ваш датасет в формате CSV. Если вы еще не знаете, что хотите проанализировать, то бот поделится ссылкой на датасеты Kaggle. 
   - После загрузки датасета бот автоматически проанализирует датасет, опишет признаки и укажет, какая переменная подходит под роль таргета
   - Затем бот отправит второе сообщение, где подскажет, какие еще признаки можно добавить для лучшего объяснения целевой переменной.
   - После этого можно задавать вопросы по датасету текстом или голосом
      - К сожалению, не успели добавить возможность строить графики и изображения

### 4.3. Сценарий "Объяснение IT мемов"

- Если вы выбрали этот сценарий, бот будет объяснять вам IT-мемы, связанные с Data Science и IT-индустрией, загруженные в форме картинок.
- Чтобы получить объяснение мема, вам нужно загрузить мем в виде одного изображения через сообщения.
- Бот проанализирует элементы мема, которые вызывают смех, основную идею или шутку, заложенную в меме, а также наличие каких-либо культурных или интернет-отсылок, которые следует знать, чтобы понять мем.
- Далее, по кнопке, бот может сформировать для вас сообщение-реакцию, которое можно использовать в ответ на мем. Сообщение покажет коллегам, что вы поняли суть изображения.
- Вы также можете вступить в диалог с ботом и задавать вопросы о картинке, которую вы загрузили.

Обратите внимание, что бот использует искусственный интеллект и может отвечать на широкий спектр вопросов. Однако, он не всегда может гарантировать 100% точность или полноту ответов. В случае сложных или специфических вопросов, рекомендуется обратиться к дополнительным источникам информации или специалистам в соответствующей области.

# Техническая документация

Библиотеки:

- [openai](https://pypi.org/project/openai/)
- [python-telegram-bot](https://pypi.org/project/python-telegram-bot/)
- [Jupyter Notebook](https://pypi.org/project/notebook/)

## Структура проекта

```
ds-newcomer-bot/
│
├── config/
│   ├─── openai_client.py
│   ├─── telegram_bot.py
│   └─── tokens.py
│
├── exceptions/
│   ├─── bad_argument_error.py
│   └─── bad_choice_error.py
│
├── handlers/
│   ├── __init__.py
│   ├── command_handlers.py
│   └── message_handlers.py
│
├── utils/
│   ├── constants.py
│   ├── dialog_context.py
│   ├── helpers.py
│   ├── prompts.py
│   └── utils.py
│
├── app.py
├── Dockerfile
├── Makefile
└── requirements.txt
```

- `config/` - конфигурационные файлы
- `handlers/` - обработчики сообщений и команд
- `utils/` - вспомогательные функции
- `app.py` - главный файл приложения
- `Dockerfile` - скрипт для создания Docker образа
- `Makefile` - автоматизация процесса сборки
- `requirements.txt` - зависимости проекта

---

# Часть 0: Создание репозитория

- нажми кнопку справа сверху **USE THIS TEMPLATE**
- назови проект
- контент в репозитории будет использоваться для хакатона

---
  
# Часть 1: Локальная установка

Для локальной установки проекта потребуется:

- подключение к VPN серверу для доступа к API OpenAI
- токен Telegram бота
- токен API OpenAI
- операционная система Linux или MacOS

## Токен Телеграм бота

Для начала нужно получить токен для доступа к HTTP API вашего бота:

1. Найдите в Telegram бота `@BotFather`
2. Отправьте ему команду `/newbot`
3. Введите имя проекта и имя бота
4. Скопируйте полученный токен

## Установка проекта

0. Склонировать репозиторий

   ```
   git clone github.com/yourreponame
   ```

2. В `Makefile` введите токены Telegram и OpenAI:

   ```
   TELEGRAM_BOT_TOKEN=1235
   OPENAI_API_KEY=1234
   ```

3. Установка зависимостей, генерация файла `.env`:

   ```
   make setup
   ```

## Запуск проекта

1. Запускаем бота локально

   ```
   make run
   ```

2. Открываем Telegram бота и отправляем сообщение

   > Сообщения в Telegram боте и в терминале дублируются.

3. Для удаления .venv, .env, cache и других временных файлов:

   ```
   make clean
   ```

---

# Часть 2: Разработка на облачном сервере

Для удаленной разработки потребуется:

- Доступ к Серверу (ssh user@ip & password)
- Jupyter Notebook
- Visual Studio Code

#### Предустановленный софт на сервере

- vim
- build-essential
- python3
- python3-venv
- docker-ce
- docker-ce-cli
- docker-buildx-plugin
- docker-compose-plugin

# Удаленная разработка

0. Заходим на сервер

  ```
  ssh -i PATH_TO_YOUR_KEY.pem admin@SERVER_IP_ADDRESS
  ```

1. Клонируем (по https) свой репозиторий в отдельную папку на сервер

   ```
   git clone <repositorylink>
   ```

3. В `Makefile` введите токены Telegram и OpenAI:

   ```
   TELEGRAM_BOT_TOKEN=1235
   OPENAI_API_KEY=1234
   ```

4. Установка зависимостей, генерация файла `.env`:

   ```
   make setup
   ```

5. Запускаем Jupyter Notebook

   ```
   make notebook
   ```

6. Копируем после **token=** в заметки:

   ```
   http://127.0.0.1:8888/tree?token=YOUR_PERSONAL_TOKEN
   ```

7. На своем **персональном устройстве** создаем туннель:

   ```
   ssh -NL 8888:localhost:8888 root@SERVER_IP_ADDRESS
   ```

   или (в зависимости от того, как вы залогинены на сервере)

   ```
   ssh -NL 8888:localhost:8888 admin@SERVER_IP_ADDRESS
   ```

  также если вы залогинены на сервере с использованием ключа (-i PATH_TO_YOUR_KEY.pem), его нужно указать при создании тунеля

9. Открываем в браузере;

   ```
   http://localhost:8888
   ```

10. Вставляем токен, который скопировали на шаге **5**, в поле "Password or token" и нажимаем Login.
11. Пользуемся

---

# Запуск Docker контейнера

Для деплоя контейнера на облачный сервер потребуется:

- Скаченная программа [Docker](https://www.docker.com/products/docker-desktop/)
- Аккаунт в [DockerHub](https://hub.docker.com/)
- [Создать репозиторий](https://docs.docker.com/docker-hub/repos/create/)
- токен Telegram бота
- токен API OpenAI
- операционная система Linux или MacOS

1. В `Makefile` добавим к уже имеющимся токенам, **username** и **repositoryname**:

   ```
   # данные пользователя на Docker Hub
   USERNAME=UserNameDockerHub
   REPO=RepositoryNameDockerHub
   TAG=v1
   TELEGRAM_BOT_TOKEN=1235
   OPENAI_API_KEY=1234
   ```

#### Для публикации образа в [DockerHub](https://hub.docker.com/) нужно залогиниться через CLI командой `docker login`

2. Собираем образ под Linux Debian:

   ```
   make build
   ```

3. Запускаем контейнер с приложением

  ```
   make dockerrun
  ```

4. Также, можно опубликовать образ в DockerHub:

   ```
   make push
   ```

---

## Скачивание и запуск опубоикованного образа

1. Находим опубликованный образ в DockerHub:

   ```
   docker search username/projectname
   ```

2. Скачиваем образ:

   ```
   docker pull username/projectname:v1
   ```

3. Запускаем контейнер с токенами Telegram бота и OpenAI API:

   ```
   sudo docker run -i -t -e TELEGRAM_BOT_TOKEN=YOURTOKEN -e OPENAI_API_KEY=YOURTOKEN username/projectname:v1
   ```

4. Открываем Telegram бота и отправляем сообщение
   > Сообщения в Telegram боте и в терминале дублируются.

## Линтеры

Выберете интерпретатор из .venv в VSCode.

Установите в VSCode плагины:

- ms-python.black-formatter
- ms-python.mypy-type-checker
- charliermarsh.ruff

После этого они автоматически будут применяться к коду.
