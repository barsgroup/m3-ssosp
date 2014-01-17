#coding:utf-8
import zlib
import base64
import time
import uuid


# http://stackoverflow.com/questions/1089662/python-inflate-and-deflate-implementations
def decode_base64_and_inflate(b64string):
    u"""
    Разкодировать из base64 и разжать zip
    """
    decoded_data = base64.b64decode(b64string)
    return zlib.decompress(decoded_data, -15)


def decode_base64(b64string):
    u"""
    Разкодировать из base64
    """
    decoded_data = base64.b64decode(b64string)
    return decoded_data


def deflate_and_base64_encode(string_val):
    u"""
    Сжать zip и закодировать в base64
    """
    zlibbed_str = zlib.compress(string_val)
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string)


def get_random_id():
    random_id = '_' + uuid.uuid4().hex
    return random_id


def get_time_string(delta=0):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(time.time() + delta))
