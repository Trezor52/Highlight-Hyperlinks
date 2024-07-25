# -*- coding: utf-8 -*-
import re
import sys
from requests import RequestException
import requests

from g4f.client import Client
import time
import logging
import my_prompts
from g4f.Provider import RetryProvider, ChatgptFree, DuckDuckGo, DeepInfra, FreeChatgpt, HuggingFace, Aura, \
    You, ChatgptNext, Koala, OpenaiChat, Aichatos
import g4f.debug

g4f.debug.logging = True
sys.tracebacklimit = 0


def send_messages_to_gpt(content) -> str:
    """
    Функция для отправки запроса нейросети ChatGPT
    :param content: Содержимое, промпт или любое другое сообщение
    :return:
    """
    num_retry = 5
    for _ in range(num_retry):
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-3.5-turbo",
                stream=False,
                messages=content,
                ignored=None,
                provider=RetryProvider([
                    Aichatos, # зачастую выдает бан на 2 минуты и больше за большое количество запросов, но надежный
                    You,
                    ChatgptNext, Koala,
                    OpenaiChat, ChatgptFree,
                    DuckDuckGo, DeepInfra,
                    FreeChatgpt, HuggingFace, Aura
                ], shuffle=False)
            )
            return response
        except Exception as e:
            logging.error(str(e), exc_info=True)
    return


def get_phones_from_text(text):
    # Получение отформатированного текста от нейросети - выделение телефонов фигурными скобками
    prompt_phones = my_prompts.prompt_1
    prompt_phones += text
    prompts = [{"role": "user", "content": prompt_phones}]
    return send_messages_to_gpt(content=prompts)


def get_mails_from_text(text):
    # Получение отформатированного текста от нейросети - выделение почт фигурными скобками
    prompt_mails = my_prompts.prompt_2
    prompt_mails += text
    prompts = [{"role": "user", "content": prompt_mails}]
    return send_messages_to_gpt(content=prompts)


def get_links_from_text(text):
    # Получение отформатированного текста от нейросети - выделение ссылок фигурными скобками
    prompt_links = my_prompts.prompt_3
    prompt_links += text
    prompts = [{"role": "user", "content": prompt_links}]
    return send_messages_to_gpt(content=prompts)


def telephone_formating(text):
    assembly_text = []  # список сборного текста

    for line in text:  # рассматриваем пошагово каждую строку текста

        # line = line.rstrip('\n') # избавление от \n в конце строки, чтобы не мешался

        bracket_open_find = re.search('{', line) # нахождение фигурной открывающейся скобки
        bracket_close_find = re.search('}', line) # нахождение фигурной закрывающейся скобки

        if bracket_open_find == None:

            line += '\n'  # добавка \n в конец строки, чтобы было понятно, что это конец исходной строки
            assembly_text.append(line)  # всю строку добавить в сборный текст

        else:

            while (bracket_open_find != None) and (bracket_close_find != None):
                assembly_text.append(
                    line[0:bracket_open_find.start()])  # запись всего до фигурной открывающей скобки в сборный текст

                rough_line = line[bracket_open_find.end():bracket_close_find.start()] # вытаскивание всего, что находится в фигурных скобках в качестве грубой строки
                telephone = line[bracket_open_find.end():bracket_close_find.start()]  # вытаскивание всего, что находится в фигурных скобках в качестве номера телефона
                telephone = ''.join(telephone.split())  # удаление всех пробельных символов
                telephone = telephone.replace('+7', '8')  # замена +7 на 8
                telephone = telephone.replace('(', '')  # удаление всех открывающихся скобочек
                telephone = telephone.replace(')', '')  # удаление всех закрывающихся скобочек
                telephone = telephone.replace('-', '')  # удаление всех тире

                phone_pattern = re.compile(r"\+?\d{1}\d{3}\d{3}\d{2}\d{2}\b") # шаблон телефонного номера
                phone_check = re.match(phone_pattern, telephone) # проверка на совпадения телефонного номера и шаблона
                if (phone_check != None): # если шаблон прошел
                    if (telephone[len(telephone) - 1] == ','): # если оканчивается на запятую
                        telephone = telephone[:(len(telephone) - 1)] # удаляем эту запятую
                        testing_link = "https://wa.me/" + telephone # составляем тестовую ссылку для проверки запроса
                        response = requests.get(testing_link) # получаем ответ на запрос
                        if response: # если запрос прошел
                            assembly_text.append('[*t*')  # открываем квадратные скобки и добавляем префикс для определения номера телефона
                            assembly_text.append(telephone)  # записываем отформатированный номер телефона
                            assembly_text.append('],')  # закрываем квадратные скобки и дописываем удаленную запятую вне скобок
                        else: # если запрос не прошел
                            assembly_text.append('[')  # открываем квадратные скобки, но не добавляем префикс для определения номера телефона
                            assembly_text.append(telephone)  # записываем отформатированный номер телефона
                            assembly_text.append('],')  # закрываем квадратные скобки и дописываем удаленную запятую
                    else: # если не оканчивается на запятую
                        testing_link = "https://wa.me/" + telephone # составляем тестовую ссылку для проверки запроса
                        response = requests.get(testing_link) # получаем ответ на запрос
                        if response: # если запрос прошел
                            assembly_text.append('[*t*')  # открываем квадратные скобки и добавляем префикс для определения номера телефона
                            assembly_text.append(telephone)  # записываем отформатированный номер телефона
                            assembly_text.append(']')  # закрываем квадратные скобки
                        else: # если запрос не прошел
                            assembly_text.append('[')  # открываем квадратные скобки, но не добавляем префикс для определения номера телефона
                            assembly_text.append(telephone)  # записываем отформатированный номер телефона
                            assembly_text.append(']')  # закрываем квадратные скобки
                else: # если шаблон не прошел
                    assembly_text.append(rough_line)  # записываем грубую строку

                line = line[bracket_close_find.end():]  # оставляем от исходной строки только то, что идет после фигурной закрывающейся скобки

                bracket_open_find = re.search('{', line)  # поторное нахождение фигурной открывающейся скобки
                bracket_close_find = re.search('}', line)  # повторное нахождение фигурной закрывающейся скобки

            line += '\n'  # добавка \n в конец к оставшейся части строки, чтобы было понятно, что это конец исходной строки
            assembly_text.append(line)  # все, что осталось, добавить в сборный текст

    output = ''.join(assembly_text)  # получение готового отформатированного текста
    return output


def email_formating(text):
    assembly_text = []  # список сборного текста

    for line in text:  # рассматриваем пошагово каждую строку текста

        # line = line.rstrip('\n') # избавление от \n в конце строки, чтобы не мешался

        bracket_open_find = re.search('{', line) # нахождение фигурной открывающейся скобки
        bracket_close_find = re.search('}', line) # нахождение фигурной закрывающейся скобки

        if bracket_open_find == None:

            line += '\n'  # добавка \n в конец строки, чтобы было понятно, что это конец исходной строки
            assembly_text.append(line)  # всю строку добавить в сборный текст

        else:

            while (bracket_open_find != None) and (bracket_close_find != None):
                assembly_text.append(line[0:bracket_open_find.start()])  # запись всего до фигурной открывающей скобки в сборный текст

                rough_line = line[bracket_open_find.end():bracket_close_find.start()] # вытаскивание всего, что находится в фигурных скобках в качестве грубой строки
                email = line[bracket_open_find.end():bracket_close_find.start()]  # вытаскивание всего, что находится в фигурных скобках в качестве электронной почты
                email = ''.join(email.split())  # удаление всех пробельных символов
                if (email[len(email) - 1] == ','): # если оканчивается на запятую
                    email = email[:(len(email) - 1)] # удаляем эту запятую
                    email = email.replace(',', '.')  # замена всех запятых на точки
                    email = email + ',' # дописываем удаленную запятую
                else: # если не оканчивается на запятую
                    email = email.replace(',', '.')  # замена всех запятых на точки

                email_pattern = re.compile(r"[а-яА-Яa-zA-Z0-9.+-]+@[а-яА-Яa-zA-Z0-9-]+\.[а-яА-Яa-zA-Z0-9.-]+\b") # шаблон электронной почты
                email_check = re.match(email_pattern, email) # проверка на совпадения электронной почты и шаблона
                if (email_check != None): # если шаблон прошел
                    if (email[len(email) - 1] == ','): # если оканчивается на запятую
                        email = email[:(len(email) - 1)] # удаляем эту запятую
                        assembly_text.append('[*m*')  # открываем квадратные скобки и добавляем префикс для определения электронной почты
                        assembly_text.append(email)  # записываем отформатированную электронную почту
                        assembly_text.append('],')  # закрываем квадратные скобки и дописываем удаленную запятую
                    else: # если не оканчивается на запятую
                        assembly_text.append('[*m*')  # открываем квадратные скобки и добавляем префикс для определения электронной почты
                        assembly_text.append(email)  # записываем отформатированную электронную почту
                        assembly_text.append(']')  # закрываем квадратные скобки
                else: # если шаблон не прошел
                    assembly_text.append(rough_line)  # записываем грубую строку

                line = line[bracket_close_find.end():]  # оставляем от исходной строки только то, что идет после фигурной закрывающейся скобки

                bracket_open_find = re.search('{', line)  # поторное нахождение фигурной открывающейся скобки
                bracket_close_find = re.search('}', line)  # повторное нахождение фигурной закрывающейся скобки

            line += '\n'  # добавка \n в конец к оставшейся части строки, чтобы было понятно, что это конец исходной строки
            assembly_text.append(line)  # все, что осталось, добавить в сборный текст

    output = ''.join(assembly_text)  # получение готового отформатированного текста
    # print(output)
    return output


def site_formating(text):
    assembly_text = []  # список сборного текста

    for line in text:  # рассматриваем пошагово каждую строку текста

        # line = line.rstrip('\n') # избавление от \n в конце строки, чтобы не мешался

        bracket_open_find = re.search('{', line) # нахождение фигурной открывающейся скобки
        bracket_close_find = re.search('}', line) # нахождение фигурной закрывающейся скобки

        if (bracket_open_find == None):

            line += '\n'  # добавка \n в конец строки, чтобы было понятно, что это конец исходной строки
            assembly_text.append(line)  # всю строку добавить в сборный текст

        else:

            while (bracket_open_find != None) and (bracket_close_find != None):
                assembly_text.append(line[0:bracket_open_find.start()])  # запись всего до фигурной открывающей скобки в сборный текст

                rough_line = line[bracket_open_find.end():bracket_close_find.start()] # вытаскивание всего, что находится в фигурных скобках в качестве грубой строки
                site = line[bracket_open_find.end():bracket_close_find.start()]  # вытаскивание всего, что находится в фигурных скобках в качестве сайта
                site = ''.join(site.split())  # удаление всех пробельных символов
                site = site.replace(';', ':')  # замена ; на :
                site = site.replace('\\', '/')  # замена \ на /
                if (site[len(site) - 1] == ','): # если оканчивается на запятую
                    site = site[:(len(site) - 1)] # удаляем эту запятую
                    site = site.replace(',', '.')  # замена всех запятых на точки
                    site = site + ',' # дописываем удаленную запятую
                else: # если не оканчивается на запятую
                    site = site.replace(',', '.')  # замена всех запятых на точки

                site_pattern = re.compile(r"https://[а-яА-Яa-zA-Z0-9/]+\.[а-яА-Яa-zA-Z0-9./]+|http://[а-яА-Яa-zA-Z0-9/]+\.[а-яА-Яa-zA-Z0-9./]+|[а-яА-Яa-zA-Z0-9/]+\.[а-яА-Яa-zA-Z0-9./]+") # шаблон ссылки на сайт
                site_check = re.match(site_pattern, site) # проверка на совпадения ссылки на сайт и шаблона
                comma_flag = 0 # флаг окончания на запятую изначально опущен

                if (site_check != None): # если шаблон прошел
                    if (site[len(site) - 1] == ','): # если оканчивается на запятую
                        site = site[:(len(site) - 1)] # удаляем эту запятую
                        comma_flag = 1 # флаг окончания на запятую поднять
                    site = site.replace('https://', '') # убираем https://
                    site = site.replace('http://', '') # убираем http://
                    testing_link = "https://" + site # составляем тестовую ссылку для проверки запроса
                    try:
                        response = requests.get(testing_link) # получаем ответ на запрос
                        response.raise_for_status()
                    except requests.exceptions.ConnectionError:  # если ошибка неполученного ответа
                        assembly_text.append('[')  # открываем квадратные скобки, но не добавляем префикс для определения ссылки на сайт
                        assembly_text.append(site)  # записываем отформатированную ссылку на сайт
                        assembly_text.append(']')  # закрываем квадратные скобки
                        if (comma_flag == 1): # если поднят флаг окончания на запятую
                            assembly_text.append(',') # добавить в сборный текст запятую
                    except Exception: # если любая другая ошибка
                        assembly_text.append('[')  # открываем квадратные скобки, но не добавляем префикс для определения ссылки на сайт
                        assembly_text.append(site)  # записываем отформатированную ссылку на сайт
                        assembly_text.append(']')  # закрываем квадратные скобки
                        if (comma_flag == 1): # если поднят флаг окончания на запятую
                            assembly_text.append(',') # добавить в сборный текст запятую
                    else: # если ответ получен успешно
                        assembly_text.append('[*s*')  # открываем квадратные скобки и добавляем префикс для определения ссылки на сайт
                        assembly_text.append(site)  # записываем отформатированную ссылку на сайт
                        assembly_text.append(']')  # закрываем квадратные скобки
                        if (comma_flag == 1): # если поднят флаг окончания на запятую
                                assembly_text.append(',') # добавить в сборный текст запятую
                else: # если шаблон не прошел
                    assembly_text.append(rough_line)  # записываем грубую строку

                line = line[bracket_close_find.end():]  # оставляем от исходной строки только то, что идет после фигурной закрывающейся скобки

                bracket_open_find = re.search('{', line)  # поторное нахождение фигурной открывающейся скобки
                bracket_close_find = re.search('}', line)  # повторное нахождение фигурной закрывающейся скобки

            line += '\n'  # добавка \n в конец к оставшейся части строки, чтобы было понятно, что это конец исходной строки
            assembly_text.append(line)  # все, что осталось, добавить в сборный текст

    output = ''.join(assembly_text)  # получение готового отформатированного текста
    # print(output)
    return output


def html_converter(massive):
    new_massive = [] # массив всех слов в тексте
    for word in massive: # для каждого слова
        if re.search('\[\*t\*', word) != None: # если это телефонный номер
            word = word.replace('[*t*', '') # удаляем квадратную открывающуюся скобку с префиксом
            word = word.replace(']', '') # удаляем квадратную закрывающуюся скобку
            if word[len(word) - 1] == ',':
                word = word[:(len(word) - 1)]
                link = "https://wa.me/" + word  # формируем ссылку на Вотсап
                word = f'<a href ="{link}">{word}</a>,'  # форматируем под html
            elif word[len(word) - 1] == '.':
                word = word[:(len(word) - 1)]
                link = "https://wa.me/" + word  # формируем ссылку на Вотсап
                word = f'<a href ="{link}">{word}</a>.'  # форматируем под html
            else:
                link = "https://wa.me/" + word  # формируем ссылку на Вотсап
                word = f'<a href ="{link}">{word}</a>'  # форматируем под html

        if re.search('\[\*m\*', word) != None: # если это электронная почта
            word = word.replace('[*m*', '') # удаляем квадратную открывающуюся скобку с префиксом
            word = word.replace(']', '') # удаляем квадратную закрывающуюся скобку
            if word[len(word) - 1] == ',':
                word = word[:(len(word) - 1)]
                word = f'<a href = mailto:{word}>{word}</a>,'  # форматируем под html
            elif word[len(word) - 1] == '.':
                word = word[:(len(word) - 1)]
                word = f'<a href = mailto:{word}>{word}</a>.'  # форматируем под html
            else:
                word = f'<a href = mailto:{word}>{word}</a>'

        if re.search('\[\*s\*', word) != None: # если это название сайта или ссылка на сайт
            word = word.replace('[*s*', '') # удаляем квадратную открывающуюся скобку с префиксом
            word = word.replace(']', '') # удаляем квадратную закрывающуюся скобку
            if word[len(word) - 1] == ',':
                word = word[:(len(word) - 1)]
                link = "https://" + word  # формируем целую ссылку
                word = f'<a href ="{link}">{word}</a>,'  # форматируем под html
            elif word[len(word) - 1] == '.':
                word = word[:(len(word) - 1)]
                link = "https://" + word  # формируем целую ссылку
                word = f'<a href ="{link}">{word}</a>.'  # форматируем под html
            else:
                link = "https://" + word # формируем целую ссылку
                word = f'<a href ="{link}">{word}</a>' # форматируем под html

        new_massive.append(word) # добавляем в массив
    return new_massive


def get_hyperlinks(file_path: str, output_file_path: str):
    """
    :param file_path: path (name) of the input file with text (without extension)
    :param output_file_name: path (name) of the output to save the result
    :return: EN: html and txt files with hyperlinks
            RU: html и txt файлы с гиперссылками
    """
    file_path += ".txt"
    data = []
    input_text = ''  # Сюда идёт текст из файла

    with open(file_path, 'r', encoding='utf-8') as infile:  # Открываем файл с текстом
        for line in infile:
            for word in line.split():
                data.append(word)  # Разбиваем текст на слова и записываем их в список data
            data.append("<br>") # Добавляем перенос строки для будущего преобразования в html
    for i in data:  # Собираем по новой строку для нейронки. Переменную infile нейронка не воспринимает, пришлось использовать костыли
        input_text = input_text + ' ' + i  # Вставляем текст из файла

    # Запрос к GPT и форматирование тел гиперссылок в тексте
    # Все команды print - для проверки результатов

    received_phones_text = get_phones_from_text(input_text) # Выделение номеров нейросетью
    phones_ready = telephone_formating(received_phones_text.split('\n'))  # Редактируем текст с телефонами и ставим индекс *t*
    # print(received_phones_text)
    # print(phones_ready)
    received_emails_text = get_mails_from_text(phones_ready) # Выделение почт нейросетью
    emails_ready = email_formating(received_emails_text.split('\n'))  # Редактируем текст с почтами и ставим индекс *m*
    # print(received_emails_text)
    # print(emails_ready)
    received_links_text = get_links_from_text(emails_ready) # Выделение ссылок нейросетью
    links_ready = site_formating(received_links_text.split('\n'))  # Редактируем текст с сайтами и ставим индекс *s*
    # print(received_links_text)
    # print(links_ready)

    # В переменной links_ready будет находиться весь текст с уже найденными ссылками и тд.
    word_arr_final_text = links_ready.split()  # Опять разбиваем текст на отдельные слова
    # Далее для замены этих слов на гиперссылки необходимо очистить сам текст, преобразованный нейронкой, от квадратных скобочек и индексов
    edited_text = html_converter(word_arr_final_text) # финальный текст без лишних символов и с встроенными гиперссылками для html

    # Подготовка к выводу в html формате
    html_body = '<html>' + '\n' + '   <body>' + '\n' + (
        '       <h1>Готовый текст </h1>') + '\n' + '        <p>'  # html разметка для нормального вида
    for i in edited_text:  # Записываем исправленный текст в строку с html разметкой
        html_body = html_body + i + ' '
    html_body = html_body + '        </p>' + '\n' + '    </body>' + '\n' '</html>'  # Конец html разметки
    with open(output_file_path + '.html', 'w', encoding='utf-8') as outfile:  # Открываем или создаем html файл
        outfile.write(html_body)  # Записываем новый текст в файл
    with open(output_file_path + '.txt', 'w', encoding='utf-8') as outfile:  # Открываем или создаем txt файл
        outfile.write(html_body)  # Записываем новый текст в файл
    print('''@@@@@@%%%##******************************************************##%%%@@@
    @@@@@%%###***********************************************+++++++**###%@@@
    @@@%%%###*+++*+++***********************************+*++++++===++**#%%%%@
    @@%%%####*++++++++++++**++++*************************++++++====+++*####%%
    @%%%#####+++=++++++++++++++++++***********************++++=====++++***##%
    %%%%%%###++=+++===++++++++++++++++++++++++++*******++*+++=====+++++***##%
    %%%###%%*++++=====+++++++++++++++++++++++++++*******+++++=====+++++****##
    %%%%%%%%*++==--==++++++++++++++++++++++++++++++++++++++===========+****##
    @%#%%%%%++=---=++++++==+====+++++++++++++++++++++++++++===========******#
    @@%%%%%%+=--==+++++++==========+++++++++++++++++++++++============******#
    @@@%%%#*=-==+++++++++======================++++++++++============*******#
    @@@%%##===++++++++++++==========++=====----===+++++==============*******#
    %%%%##+++++++++**##*+++========++++++====-----=================-********#
    %%%%##*+++**##%%%%#++++#+=====++++++=======----====--=========-+*******#%
    #%%%%%%%%%%%%@%%#*+++++*%#*+++++++++++=========-------=======-=#****##%%#
    ###@%%@@@@%%#**++++++++++*%%##********+++++++==-------=======+##**#%@#*##
    #####%%%%*+++++++++++++++++*%%%%%%%%%%%%%#*+++==-----===+===+####@%#***##
    #####%%%%#++++++++++++++++++++*#%@@@@@%%%%%#*++=-----=+++==*###@%#****###
    ##%%%%%%%%%#+++++++++++++++++++++++**#%@@%%%#*+=----=+++=+###@%###**#####
    %%%%%%%%%%%%%%*+*##***++++++++++++++++++*#%%%#*=---=++++##%@%############
    %%%%%%%%%%%%%%@%=+@@@#*++************++++++*##*=---++#@%@@@%#############
    %%%%%%%%%%%%%%@-:=%@@@#++******#%%%##***+++++**=--=+%#+-%%%##############
    %%%%%%%%%%%@@@@.:#@@#%%++****##+=#@@@@%#******+=--+#*+*#%%%%%############
    %%%%%%%@@@@%@%#*:*###%%++*+*##-.*%@%%%@@#*****=--**+##%@@%%%%%%##########
    %%%%%@@@%@@@@#+**#####=++++*%+:=#@%+@%%*@#+++=--****%@@@@%%%%%%%#########
    %%%@%%@@@@@@@#=++***+==+++**#*--##@@#%+-#+--::-=++#@@@@@@@@%%%%%%%%%%%%%%
    %%%%#@@@@@@@@#==++====+*****###==*##%+*#+-::::=#@@@@@@@@@@@@@%%%%%%%%%%%%
    %@@@@##%%##%%%=+++===+***++**###**##***=--:::=@@%@@@@@@@@@@@@@@@%%%%%%%%%
    @@@@@@@@%#%@#%*+=--=++**+++++++****++====---+%%%%% NO SWITCHES??? %%%%%%%
    @@@@@@@@@%%@%@#=--=++++++++++++++++++++++==+####%%%%%@@@@@@@@@@@@@@@@%%%%
    @@@@@@@@@%####=--========+++++++******+++==*%%*###%%%%%**@@@@@@@@@@@@@@%%
    @@@@@@@@@%###+--==---::--===+*******++++=-%==*######%#%+%@@@@@@@@@@@@@@@@
    @@@@@@@@@@##*-----::.::--===+*****+++++=-#@**#***###%@##%@@@@@@@@@@@@@@@@
    @@@@@@@@%%%*--::::::::---=+********++==-*@@@%@%###########%@@@@@@@@@@@@@@
    @@@@@@%%%%+---::..:::-=++++++*****++=--*@@@@@@@@%%%%%%%#####%%@@@@@@@@@@@
    @@@@@%%%%@%++=--::--===-----=+***++=--+@@@@@@@@@@@@@@@%%%%####%%%@@@@@@@@
    @@@@%%%%%@%%**++++++=--:::::-=+**+=--*@@@@@@@@@@@@@@@@%%@%%%%%%%@%%@@@@@@
    @@@@%%%%@@@@@%%+*#*#**+===++--=*++==#@@@@@@@@@@@@@@@@@@@@@@@@%%%@@@@@@@@@
    @@@@%%%%@@@@%%%+*%%%#**+==--=*=*+==*%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    @@%%@@@@@@@@@%#+#%%%#*****++==**++##%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@''')
    return 0
