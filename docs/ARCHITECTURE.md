# Архитектура проекта
## Структура
```
exercise_generator/
├── README.md                    # Пользовательская документация
├── requirements.txt             
├── .gitignore                   
├── .github/
│   └── workflows/
│       └── ci.yml               
│
├── src/
│   └── exercise_generator/
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── text_processor.py        # Обработка текстов
│       │   └── document_loader.py       # Загрузка разных форматов
│       │
│       ├── exercises/
│       │   ├── __init__.py
│       │   ├── base.py                 # Базовый класс упражнения
│       │   ├── word_order.py           # Перестановки слов
│       │   ├── fill_blanks.py          # Вставка слов
│       │   ├── multiple_choice.py      # Множественный выбор
│       │   ├── matching.py             # Соответствие
│       │   └── true_false.py           # Верно/Неверно
│       │
│       ├── generators/
│       │   ├── __init__.py
│       │   └── exercise_generator.py   # Основной класс генератора
│       │
│       ├── formatters/
│       │   ├── __init__.py
│       │   └── docx_formatter.py       # Форматирование в docx
│       │
│       └── web/
│           ├── app.py                  # Запуск локального сервера
│           └── templates/
│               ├── about.html          # Страница с информацией
│               └── index.html          # Основная страница с карточками
│
├── tests/
│   ├── __init__.py
│   ├── test_module1.py                 # Тесты для module1
│   ├── test_module2.py                 # Тесты для module2
│   └── conftest.py                     # Конфигурация pytest
│
├── docs/
│   ├── README.md                       # Техническая документация
│   └── ARCHITECTURE.md                 # Архитектура проекта
│
├── .pylintrc                    
└── pytest.ini
```
[описание классов и модулей]
## Диаграммы
[UML или текстовые диаграммы]
## Взаимодействие компонентов
[описание как работают части]
