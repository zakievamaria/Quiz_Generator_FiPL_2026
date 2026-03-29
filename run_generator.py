from src.generators.exercise_generator import ExerciseGenerator
import os

if __name__ == "__main__":
    # 1. Создаем генератор
    generator = ExerciseGenerator(language='french')

    folder_path = "Корпус французских текстов"

    text_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith('.txt')
    ]

    generator.load_texts(text_files)

    # 3. Генерируем упражнения
    exercises = generator.generate_exercises(num_per_type=3)

    # 4. Сохраняем задания
    generator.save_exercises(exercises, "exercises.docx")

    # 5. Сохраняем ответы
    generator.save_answers(exercises, "answers.docx")