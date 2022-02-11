import os
import random

questions_dir = os.path.join(os.path.dirname(__file__), 'questions')
files = os.listdir(questions_dir)
random_questions_file = random.choice(files)

file_path = os.path.join(questions_dir, random_questions_file)
with open(file_path, encoding='KOI8-R') as file_with_questions:
    questions = file_with_questions.read()

print(questions)
