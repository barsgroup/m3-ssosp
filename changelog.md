# История изменений

**1.2.0**
- Изменения для совместимости с Django 1.8

**1.1.5**

- Подключение m3-django-compat для совместимости с разными версиями Django
- Переход на миграции Django

**1.1.4**

- Получение настроек вынесено в settings.py
- Исправлены ошибки, возникающие из-за истечения времени сессии
- Добавлены миграции, если БД используется в качестве бэкенда
- Исправлена ошибка загрузки ключей цифровой подписи

**1.1.3**

- Обработка исключения при авторизации в приложении 
- Документация: настройка цифровой подписи и ее проверки / бэкенды хранения соостветствия сессий 
- Подписывание и проверка цифровой подписи в SAML-запросах 
