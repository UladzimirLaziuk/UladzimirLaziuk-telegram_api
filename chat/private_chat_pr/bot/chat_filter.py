import re
from bot.models import Obscenity
from django.db.models import Value as V
from django.db.models.functions import StrIndex
from bs4 import BeautifulSoup
from .apps import logger


d = {'а': ['а', 'a', '@'],
     'б': ['б', '6', 'b'],
     'в': ['в', 'b', 'v'],
     'г': ['г', 'r', 'g'],
     'д': ['д', 'd'],
     'е': ['е', 'e', 'ё',],
     # 'ё' : ['ё', 'e'],
     'ж': ['ж', 'zh', '*'],
     'з': ['з', '3', 'z'],
     'и': ['и', 'u', 'i', 'й'],
     # 'й': ['й', 'u', 'i'],
     'к': ['к', 'k', 'i{', '|{'],
     'л': ['л', 'l', 'ji'],
     'м': ['м', 'm'],
     'н': ['н', 'n'],
     'о': ['о', 'o', '0'],
     'п': ['п', 'n', 'p'],
     'р': ['р', 'r', 'p'],
     'с': ['с', 'c', 's'],
     'т': ['т', 'm', 't'],
     'у': ['у', 'y'],
     'ф': ['ф', 'f'],
     'х': ['х', 'x', 'h', '}{'],
     'ц': ['ц', 'c', 'u,'],
     'ч': ['ч', 'ch'],
     'ш': ['ш', 'sh'],
     'щ': ['щ', 'sch'],
     'ь': ['ь', 'b'],
     'ы': ['ы', 'bi'],
     'ъ': ['ъ'],
     'э': ['э', 'e'],
     'ю': ['ю', 'iu'],
     'я': ['я', 'ya'],
    }


def check_message(msg):
    status = 0
    # checking phone numbers presence
    result = re.findall(r'[\d\-*]{7,}', msg)
    if len(result):
        status += 2
        # print(result)
        logger.info(f'Phone number {result}')
        
    # checking emails presence
    result = re.findall(r'\w+@\w+.\w+', msg)
    if len(result):
        status += 4
        # print(result)
        logger.info(f'Email {result}')

    # checking urls presence
    pattern = r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+\
            [a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+\
            [a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\
            \.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,}'
    result = re.findall(pattern, msg)
    if len(result):
        status += 8
        # print(result)
        logger.info(f'Url {result}')

    # checking html presence
    my_bs = BeautifulSoup(msg, 'html.parser')
    result = my_bs.find(True)
    if result:
        status += 16
        # print(result)
        logger.info(f'Html content {result}')

    # checking bad words presence
    msg = msg.lower()
    for letter in msg:
        for key in d:
            if letter in d[key]:
                msg = msg.replace(letter, key)
    bw_msg = Obscenity.objects.annotate(
            msg_index=StrIndex(V(msg), 'item')
            ).filter(msg_index__gt=0)
    if bw_msg:
        status += 1
        # print(bw_msg[0].item)
        logger.info(f'Bad word {bw_msg[0].item}')

    return status
