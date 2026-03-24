from generators.exercise_generator import ExerciseGenerator

if __name__ == "__main__":
    # 1. Создаем генератор
    generator = ExerciseGenerator(language='french')

    # 2. Загружаем тексты
    generator.load_texts([
        "example1.txt",
        "example2.txt"
    ])

    # 3. Генерируем упражнения
    exercises = generator.generate_exercises(num_per_type=3)

    # 4. Сохраняем задания
    generator.save_exercises(exercises, "exercises.docx")

    # 5. Сохраняем ответы
    generator.save_answers(exercises, "answers.docx")