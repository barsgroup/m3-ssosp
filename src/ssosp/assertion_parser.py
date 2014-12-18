#coding:utf-8
u"""
Низкоуровневая работа с SAML-утверждениями (Assertion) в xml виде
с использованием lxml.etree
"""

from lxml import etree
import rsa
try:
    import xmldsig
except ImportError:
    xmldsig = None


def _build_node(builder, struct, nsmap):
    u"""
    Рекурсивный построитель элементов дерева из переданной структуры.

    :param builder: экземпляр построителя дерева etree.TreeBuilder
    :type builder: etree.TreeBuilder
    :param struct: структура, из которой надо построить дерево
    :type struct: basestring, dict, list, tuple
    :param dict nsmap: словарь замены namespace в формируемом дереве
    """
    assert isinstance(builder, etree.TreeBuilder)
    assert isinstance(nsmap, dict)
    assert isinstance(struct, (basestring, dict, list, tuple))
    if isinstance(struct, basestring):
        builder.data(struct)
    else:
        if isinstance(struct, dict):
            struct_list = [struct]
        else:
            struct_list = struct
        for item in struct_list:
            tag = item.get('tag', None)
            if tag:
                attrs = item.get('attrs', None)
                current_nsmap = item.get('nsmap', None)
                if current_nsmap:
                    nsmap.update(current_nsmap)
                # заменим неймспейс в тэге
                for key, value in nsmap.iteritems():
                    if tag.startswith('{%s}' % key):
                        tag = tag.replace('{%s}' % key, '{%s}' % value)
                        break
                builder.start(tag=tag, attrs=attrs, nsmap=current_nsmap)
                value = item.get('value', None)
                if value:
                    _build_node(builder, value, nsmap)
                builder.end(tag)


def build_assertion(assertion_struct):
    u"""
    Создание нового утверждения по структуре

    :param dict assertion_struct: словарь структуры из которого строится
        утверждение
    :return: Сформированное утверждение (Assertion, xml)
    :rtype: etree.ElementTree
    """
    assert isinstance(assertion_struct, dict)
    builder = etree.TreeBuilder()
    _build_node(builder, assertion_struct, {})
    assertion = builder.close()
    return assertion


def xml_to_assertion(xml_string):
    u"""
    Переобразование xml-строки в утверждение для дальнейшей работы

    :param basestring xml_string: Утверждение, представленное строкой
    :return: Преобразованное утверждение (Assertion, xml)
    :rtype: etree.ElementTree
    """
    assertion = etree.fromstring(xml_string)
    return assertion


def assertion_to_xml(assertion):
    u"""
    Переобразование утверждения в xml-строку

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: Утверждение представленное строкой
    :rtype: basestring
    """
    xml = etree.tostring(assertion, encoding='UTF-8', xml_declaration=True)
    return xml


def is_logout_request(assertion):
    u"""
    Проверка того, что это запрос (утверждение) на выход из системы

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: True, если запрос на выход
    :rtype: bool
    """
    logout_resp = assertion.xpath(
        '//saml2p:LogoutRequest',
        namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol'}
    )
    return len(logout_resp) > 0


def is_logout_response(assertion):
    u"""
    Проверка того, что это ответ (утверждение) на запрос на выход из системы

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: True, если ответ на запрос на выход
    :rtype: bool
    """
    logout_resp = assertion.xpath(
        '//saml2p:LogoutResponse',
        namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol'}
    )
    return len(logout_resp) > 0


def get_session_from_request_assertion(assertion):
    u"""
    Получение ID сессии из запроса на выход (утверждения)

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: идентификатор сессии
    :rtype: basestring
    """
    session_id = None
    statement = assertion.xpath(
        '//saml2p:LogoutRequest//saml2p:SessionIndex',
        namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                    'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'}
    )
    if len(statement) > 0:
        session_id = statement[0].text
    return session_id


def get_session_from_response_assertion(assertion):
    u"""
    Получение ID сессии из ответа (утверждения) на запрос

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: идентификатор сессии
    :rtype: basestring
    """
    session_id = None
    statement = assertion.xpath(
        '//saml2p:Response//saml2:Assertion//saml2:AuthnStatement',
        namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                    'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'}
    )
    if len(statement) > 0 and 'SessionIndex' in statement[0].attrib:
        session_id = statement[0].attrib['SessionIndex']
    return session_id


def get_attributes_from_assertion(assertion):
    u"""
    Получение атрибутов из утверждения

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: список атрибутов
    :rtype: list
    """
    attributes = {}
    attrs = assertion.xpath(
        '//saml2p:Response//saml2:Assertion//saml2:AttributeStatement//saml2:Attribute',
        namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                    'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'}
    )
    for attr in attrs:
        name = attr.attrib['Name']
        values = attr.xpath(
            './saml2:AttributeValue',
            namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                        'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'}
        )
        if len(values) == 0:
            # игнорируем пустые значения атрибутов
            continue
        elif len(values) == 1:
            attributes[name] = values[0].text
        else:
            # множество значений
            for value in values:
                attributes.setdefault(name, []).append(value.text)
    return attributes


def get_userid_from_assertion(assertion):
    u"""
    Получение ID пользователя из ответа (утверждения) на запрос

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :return: идентификатор пользователя
    :rtype: basestring
    """
    statement = assertion.xpath(
        '//saml2p:Response//saml2:Assertion//saml2:Subject//saml2:NameID',
        namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                    'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'}
    )
    if len(statement) > 0:
        userid = statement[0].text
    else:
        userid = None
    return userid


def verify_assertion(assertion, public_key_str):
    u"""
    Проверка цифровой подписи утверждения по публичному ключу

    :param assertion: Утверждение (Assertion, xml)
    :type assertion: etree.ElementTree
    :param basestring public_key_str: публичный ключ подписи представленный
        в виде строки
    :return: признак успешной проверки подписи
    :rtype: bool
    :raise: XMLSigException - ошибка при проверке подписи
    """
    if not xmldsig is None:
        with file(public_key_str, 'r') as public_key_file:
            public_key_data = public_key_file.read()
        public_key = rsa.key.PublicKey.load_pkcs1_openssl_pem(public_key_data)
        try:
            return xmldsig.verify(assertion.getroottree(), public_key)
        except xmldsig.XMLSigException as err:
            if err.message == "Is not signed xml!":
                return True
            else:
                raise err
    else:
        raise ImportError("Cant import xmldsig module.")


def sign_request(message, private_key_str):
    u"""
    Цифровая подпись SAML-сообщения. Получение сигнатуры по алгоритму SHA1

    :param basestring message: Сообщение для подписи
    :param basestring public_key_str: закрытый ключ для подписи представленный
        в виде строки
    :return: строка сигнатуры подписи закодированная в base64
    :rtype: basestring
    """
    with file(private_key_str, 'r') as private_key_file:
        private_key_data = private_key_file.read()
    private_key = rsa.key.PrivateKey.load_pkcs1(private_key_data)
    signed = rsa.pkcs1.sign(message, private_key, 'SHA-1')
    signature = signed.encode('base64').replace('\n', '')
    return signature
