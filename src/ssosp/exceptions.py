# coding:utf-8
u"""
Исключения
"""

class SSOLoginException(Exception):
    u""" Исключение возникающее при переходе в приложение
    """

    def __init__(self, message, next_url):
        u"""
        :param unicode message: Сообщение об ошибке
        :param unicode next_url: url на который необходимо сделать редирект
        """
        self.message = message
        self.next_url = next_url
