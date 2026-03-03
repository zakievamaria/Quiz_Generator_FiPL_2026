from generators.exercise_generator import ExerciseGenerator


def main():
    # Создаем генератор
    gen = ExerciseGenerator(language='french')

    gen.load_texts(['text'])

    # Генерируем упражнения
    exercises = gen.generate_exercises(num_per_type=2)

    # Сохраняем результаты
    gen.save_exercises(exercises, 'exercises.docx')
    gen.save_answers(exercises, 'answers_key.docx')

    print("\n✓ Проект успешно выполнен!")


if __name__ == "__main__":
    main()