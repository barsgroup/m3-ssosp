#coding:utf-8
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

try:
    from lxml import etree
except ImportError:
    from xml import etree


def _build_node(builder, struct, nsmap):
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
    """
    assert isinstance(assertion_struct, dict)
    builder = etree.TreeBuilder()
    _build_node(builder, assertion_struct, {})
    assertion = builder.close()
    return assertion


def xml_to_assertion(xml_string):
    u"""
    Переобразование xml-строки в документ для дальнейшей работы
    """
    assertion = etree.fromstring(xml_string)
    return assertion


def assertion_to_xml(assertion):
    u"""
    Переобразование xml-строки в документ для дальнейшей работы
    """
    xml = etree.tostring(assertion, encoding='UTF-8', xml_declaration=True)
    return xml


def is_logout_request(assertion):
    u"""
    Проверка того, что это запрос на выход из системы
    """
    logout_resp = assertion.xpath('//saml2p:LogoutRequest',
                                  namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol'})
    return len(logout_resp) > 0


def is_logout_response(assertion):
    u"""
    Проверка того, что это ответ на запрос на выход из системы
    """
    logout_resp = assertion.xpath('//saml2p:LogoutResponse',
                                  namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol'})
    return len(logout_resp) > 0


def get_session_from_request_assertion(assertion):
    u"""
    Получение ID сессии из запроса
    """
    session_id = None
    statement = assertion.xpath('//saml2p:LogoutRequest//saml2p:SessionIndex',
                                namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                                            'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'})
    if len(statement) > 0:
        session_id = statement[0].text
    return session_id


def get_session_from_response_assertion(assertion):
    u"""
    Получение ID сессии из ответа на запрос
    """
    session_id = None
    statement = assertion.xpath('//saml2p:Response//saml2:Assertion//saml2:AuthnStatement',
                                namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                                            'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'})
    if len(statement) > 0:
        session_id = statement[0].attrib['SessionIndex']
    return session_id


def get_attributes_from_assertion(assertion):
    """
    Returns the SAML Attributes (if any) that are present in the assertion.

    NOTE: Technically, attribute values could be any XML structure.
          But for now, just assume a single string value.
    """
    attributes = {}
    attrs = assertion.xpath('//saml2p:Response//saml2:Assertion//saml2:AttributeStatement//saml2:Attribute',
                            namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                                        'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'})
    for attr in attrs:
        name = attr.attrib['Name']
        values = attr.xpath('./saml2:AttributeValue',
                            namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                                        'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'})
        if len(values) == 0:
            # Ignore empty-valued attributes. (I think these are not allowed.)
            continue
        elif len(values) == 1:
            #See NOTE:
            attributes[name] = values[0].text
        else:
            # It has multiple values.
            for value in values:
                #See NOTE:
                attributes.setdefault(name, []).append(value.text)
    return attributes


def _get_email_from_assertion(assertion):
    """
    Returns the email out of the assertion.

    At present, Assertion must pass the email address as the Subject, eg.:

    <saml:Subject>
            <saml:NameID Format="urn:oasis:names:tc:SAML:2.0:nameid-format:email"
                         SPNameQualifier=""
                         >email@example.com</saml:NameID>
    """
    statement = assertion.xpath('//saml2p:Response//saml2:Assertion//saml2:Subject//saml2:NameID',
                                namespaces={'saml2p': 'urn:oasis:names:tc:SAML:2.0:protocol',
                                            'saml2': 'urn:oasis:names:tc:SAML:2.0:assertion'})
    if len(statement) > 0:
        email = statement[0].text
    else:
        email = None
    return email


def get_user_from_assertion(assertion):
    """
    Gets info out of the assertion and locally logs in this user.
    May create a local user account first.
    Returns the user object that was created.
    """
    email = _get_email_from_assertion(assertion)
    try:
        user = User.objects.get(email=email)
    except:
        # user = User.objects.create_user(
        #     _email_to_username(email),
        #     email,
        #     saml2sp_settings.SAML2SP_SAML_USER_PASSWORD
        # )
        return None

    #NOTE: Login will fail if the user has changed his password via the local
    # account. This actually is a good thing, I think.
    user = authenticate(username=user.username,
                        password=settings.SECRET_KEY[::-1])
    if user is None:
        raise Exception('Unable to login user "%s" with SAML2SP_SAML_USER_PASSWORD' % email)
    return user