import os

def get_notification_markdown(text, task_id):
    link = f'http://{os.getenv("CLIENT_URL")}/code/{text}/{task_id}'
    if text == 'compile':
        full_text = "Процесс сборки успешно завершен."
    elif text == 'execute':
        full_text = "Выполнение программы успешно завершен."
    elif text == 'test_execution':
        full_text = "Тестирование прошло успешно."
    else:
        full_text = text
        link = task_id
    return f"{full_text} Для продолжения работы переходите по [ссылке]({link})."

def get_notification_mail(text, task_id):
    link = f'http://{os.getenv("CLIENT_URL")}/code/{text}/{task_id}'
    if text == 'compile':
        full_text = "Процесс сборки успешно завершен."
    elif text == 'execute':
        full_text = "Выполнение программы успешно завершен."
    elif text == 'test_execution':
        full_text = "Тестирование прошло успешно."
    else:
        full_text = text
        link = task_id
    email_html = f"""
<html>
    <body>
        <p>{full_text}</p>
        <p>Для продолжения работы переходите по ссылке:</p>
        <a href="{link}">{link}</a>
    </body>
</html>
"""
    return email_html