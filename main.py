import os
import random

questions_dir = os.path.join(os.path.dirname(__file__), 'questions')
files = os.listdir(questions_dir)
random_questions_file = random.choice(files)

file_path = os.path.join(questions_dir, random_questions_file)
print(file_path)
with open(file_path, encoding='KOI8-R') as file_with_questions:
    questions = file_with_questions.read()

dict_question_answer = {}
list_questions = questions.split('Вопрос')
for question_answer in list_questions[1:]:
    if 'Ответ:' not in question_answer:
        continue
    list_question_answer = question_answer.split('Ответ:')
    question = list_question_answer[0].split(':')[1].strip()
    answer = list_question_answer[1].strip().split('\n\n')[0]
    dict_question_answer[question] = answer

print(dict_question_answer)
