#coding:utf-8
u"""
Вспомогательные утилиты

Часть утилит взята отсюда:
http://stackoverflow.com/questions/1089662/python-inflate-and-deflate-implementations
"""
import zlib
import base64
import time
import uuid


def decode_base64_and_inflate(b64string):
    u"""
    Разкодировать из base64 и разжать zip

    :param basestring b64string: исходная строка в формате base64
    :return: раскодированная и распакованная строка
    :rtype: basestring
    """
    decoded_data = base64.b64decode(b64string)
    return zlib.decompress(decoded_data, -15)


def decode_base64(b64string):
    u"""
    Разкодировать из base64

    :param basestring b64string: исходная строка в формате base64
    :return: раскодированная строка
    :rtype: basestring
    """
    decoded_data = base64.b64decode(b64string)
    return decoded_data


def deflate_and_base64_encode(string_val):
    u"""
    Сжать zip и закодировать в base64

    :param basestring string_val: исходная строка
    :return: запакованная и закодированная в base64 строка
    :rtype: basestring
    """
    zlibbed_str = zlib.compress(string_val)
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string)


def get_random_id():
    u"""
    Генерация случайного идентификатора UUID.
    Начинается с символа "_".

    :return: идентификатор в виде строки
    :rtype: basestring
    """
    random_id = '_' + uuid.uuid4().hex
    return random_id


def get_time_string(delta=0):
    u"""
    Представить текущее время в виде строки с учетом дельты.

    :param int delta: дельта времени
    :return: текущее время с дельтой в виде строки
    :rtype: basestring
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         time.gmtime(time.time() + delta))
