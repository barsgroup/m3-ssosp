Простое использование
=====================

Примеры простого использования будут основаны на :doc:`демо-приложении
<tutorial>`.

Получение дополнительных сведений о пользователе
------------------------------------------------

Сразу после установки WSO2IS и регистрации нашего приложения
не передается никаких дополнительных атрибутов пользователя.

1.  Заполним атрибуты у созданного ранее пользователя WSO2IS.

    Идем Home > Configure > Users and Roles > Users

    Находим нашего пользователя *demo*, открываем и редактируем его *User
    Profile*.

    ..  figure:: _static/images/WSO2ISUserProfile.png
        :align: center

2.  Затем укажем, какие атрибуты нужно передавать при успешной аутентификации.

    Идем Main > Manage > SAML SSO

    Находим наше приложение *saml2.demo*, открываем и редактируем его.

    Укажем признак *Enable Attribute Profile* и добавим несколько *Claim*.
    Например:

    ..  figure:: _static/images/WSO2ISEditSPAttrs.png
        :align: center

.. Note::

    Обращаю внимание, что после создания профиля атрибутов у
    зарегистрированного поставщика услуг появляется значение *Consumer Index*.
    Которое нужно указывать в настройках нашего приложения.
    Вероятно, можно создать несколько разных профилей атрибутов для одного и
    того же приложения. Но это пока не поддерживается модулем *SSOSP*.

3.  Укажем полученный *Consumer Index* в настройках settings.py:

    ::

        SSO_CONFIG = {
            'idp': 'https://localhost:9443/samlsso', # адрес Identity Provider
            'issuer': 'saml2.demo', # код связи между IdP и SP
            'acs': 'http://127.0.0.1:8000/sso/acs/', # адрес сервиса ACS
            'session_map': 'ssosp.backends.cache', # бэкенд соответствия сессий
            'get_user': 'demo.views.get_or_create_user', # получение пользователя
            'index': '1537824998', # индекс профиля атрибутов (Consumer Index)
        }

4.  Атрибуты, после входа пользователя в систему, сохраняются в сессии
    пользователя.
    Получим их при отображении страницы приложения в функции default (view.py)
    и передадим в шаблон:

    ::

        def default(request):
            attributes = request.session.get('attributes', {})
            tv = {
                'user': request.user,
                'attributes': attributes,
            }
            return render_to_response('default.html', tv)


4.  Добавим отображение атрибутов на странице приложения.

    В шаблоне default.html добавим вывод списка атрибутов.

    ::

        <html>
        <head><title>Django SAML 2.0 SP</title></head>
        <body>
        {% if not user.username %}
        I don't recognize you! Please login:<br />
        <a href="{% url login %}?next={% url default %}">Login</a>
        {% else %}
        Welcome, {{ user.username }}!<br />
        <ul>
        {% for name, value in attributes.items %}
        <li>{{ name }}: {{ value }}
        {% endfor %}
        </ul>
        <hr>
        <a href="{% url logout %}?next={% url default %}">Logout</a>
        {% endif %}
        </body>

5.  Теперь, после входа пользователя, в приложении отображаются атрибуты
    пользователя из *WSO2IS*:

    ..  figure:: _static/images/demo_attrs.png
        :align: center


Подписывание сообщений SAML
---------------------------

В *IdP* сервере *WSO2IS* есть настройка, которой можно установить возможность
использования цифровой подписи SAML-сообщений.

Идем Main > Manage > SAML SSO

Находим наше приложение *saml2.demo*, открываем и редактируем его.

    ..  figure:: _static/images/WSO2ISSigning.png
        :align: center

*Enable Assertion Signing* - признак говорит о том, что исходящие от *IdP*
сообщения будут **внутри** подписаны цифровой подписью формата XMLDSIG__.
Наше приложение может проверять корректность этой подписи.

__ http://en.wikipedia.org/wiki/XML_Signature

*Enable Signature Validation in Authentication Requests and Logout Requests* -
признак говорит о том, что приходящие на *IdP* запросы на вход и выход, будут
проверяться по сигнатуре SimpleSign__.

__ http://docs.oasis-open.org/security/saml/Post2.0/sstc-saml-binding-simplesign-cd-04.html

*Certificate Alias* - наименование сертификата, через который будут проверяться
входящие запросы. Для проверки поставим "wso2carbon".

Теперь выгрузим этот сертификат из хранилища сертификатов *WSO2IS*

::

    keytool -importkeystore -srckeystore ~/wso2is-4.6.0/repository/resources/security/wso2carbon.jks -storepass wso2carbon -destkeystore wso2carbon.p12 -deststoretype PKCS12 -srcalias wso2carbon -srcstorepass wso2carbon


Достанем из сертификата закрытый ключ. При выгрузке потребуется ввести
пароль *wso2carbon*.

::

    openssl pkcs12 -in wso2carbon.p12 -nocerts -nodes | openssl rsa > privkey.pem


Достанем также сертификат, чтобы получить из него публичный ключ.
При выгрузке потребуется ввести пароль *wso2carbon*.

::

    openssl pkcs12 -in wso2carbon.p12 -clcerts -nokeys | openssl x509 -pubkey -noout > pubkey.pem


Теперь для проверки работы с подписями добавим выгруженные ключи в настройки
settings.py и укажем признаки необходимость подписи ('signing') и проверки
подписи ('validate'):

::

    SSO_CONFIG = {

    ....

       'signing': True,
       'validate': True,
       'public_key': '''-----BEGIN PUBLIC KEY-----
    MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCUp/oV1vWc8/TkQSiAvTousMzO
    M4asB2iltr2QKozni5aVFu818MpOLZIr8LMnTzWllJvvaA5RAAdpbECb+48FjbBe
    0hseUdN5HpwvnH/DW8ZccGvk53I6Orq7hLCv1ZHtuOCokghz/ATrhyPq+QktMfXn
    RS4HrKGJTzxaCcU7OQIDAQAB
    -----END PUBLIC KEY-----''',
       'private_key': '''-----BEGIN RSA PRIVATE KEY-----
    MIICXAIBAAKBgQCUp/oV1vWc8/TkQSiAvTousMzOM4asB2iltr2QKozni5aVFu81
    8MpOLZIr8LMnTzWllJvvaA5RAAdpbECb+48FjbBe0hseUdN5HpwvnH/DW8ZccGvk
    53I6Orq7hLCv1ZHtuOCokghz/ATrhyPq+QktMfXnRS4HrKGJTzxaCcU7OQIDAQAB
    AoGAS/+ooju4a9po67zIGTEkqrQmsJC1HAPZo0bOmQK38LRzcps8Bmao9tjjbuVq
    ogEj2xgjtHyNPSn3oBUA3v33usJ6YqwVrWsC6FwmZhq8Avsf94qm4hiTHe1AdxWm
    ZGTs1eSYc6JnPIp0iVjHEfssIlGN+7LX1Q6kdbCf482dTnUCQQDvLwmtjlUASW84
    zL5PEnNCorlcJ8qjGKlbcur2Lrn3vSCyX4cIWMxPNsCGvS2IO1Ctmz7yssnobhX6
    iOaFOZVPAkEAnxuSwN4Kdw9Zku8cc7aifnJuEjzuEemM1cmwGSqilL0xUijVeeyq
    fyy+1o7VFDa/nWPmmEZSqPNR6utcvLQU9wJAIycmpPtmQsSINDDjR3vOtNx1obW3
    coENYwNgxQ3ZBzAkvhKMJg3m+T1yzlq/dmZBVUKb3c+pHSAQ2uGD/9CWwQJAVRy4
    6ndc/ce2UQWcIMJINoAcJaF2cRqQfiTAERZfllWGtr6lQ+24XwOeqsQJdCC9bAJu
    7nJf8YUIAzUYjNGAjQJBAKskkwcdhzvVcs7llm3+wWEzbMXzvNBmkZGRhDX6jtUI
    J4U9RTHivqMeym4vp0mggaD4zc8qzG1NPDOp0p5AxBg=
    -----END RSA PRIVATE KEY-----''',
    }


Приложение должно работать как прежде.


SSO и Single Logout
-------------------

При регистрации нашего приложения или позже, можно настроить возможность
*Единого выхода* для этого приложения. Для этого в описании сервисов *SSO*
*WSO2IS* нужно отметить соответствующий параметр *Enable Single Logout*.

В самом нашем приложении дополнять ничего не нужно. Выход из приложения
обрабатывается модулем *SSOSP* через сервис *ACS*.

Для проверки работы достаточно поднять копию демо-приложения, например,
на порту 9000.
Также, необходимо зарегистрировать в *WSO2IS* эту вторую копию, но
соответственно по другому адресу и с другим параметром *Issuer*.

..  figure:: _static/images/WSO2ISSecondApp.png
    :align: center

Во втором приложении необходимо соответственно поменять настройки *issuer*,
*acs* и *index* (если использовался профиль атрибутов) в settings.py.

Если изменилось имя приложения, то надо поправить ссылки *get_user* и
*ROOT_URLCONF* (у нас стало приложение demo2):

::

    ROOT_URLCONF = 'demo2.urls'

    SSO_CONFIG = {
        'idp': 'https://localhost:9443/samlsso', # адрес Identity Provider
        'issuer': 'saml2.demo2', # код связи между IdP и SP
        'acs': 'http://localhost:9000/sso/acs/', # адрес сервиса ACS
        'index': '1906473741',
        'session_map': 'ssosp.backends.cache', # бэкенд соответствия сессий
        'get_user': 'demo2.views.get_or_create_user', # получение пользователя
    }


После запуска двух приложений, при входе в первое из приложений будет запрошен
логин и пароль пользователя *WSO2IS*. При входе во второе приложение уже не
потребуется вводить логин и пароль (при условии, что это происходит в одном
браузере). **Вот оно SSO!**

..  figure:: _static/images/demo_secondapp.png
    :align: center

Теперь, при выходе из одного из приложений, на второе приложение придет запрос
о завершении сессии на адрес *ACS*. В результате, при обновлении страницы
второго приложения пользователь окажется не авторизован. Т.е. пользователь
выйдет из обоих приложений.

..  figure:: _static/images/demo_single_logout.png
    :align: center

    В истории запросов второго приложения нет обращения к /logout


Бэкенд соответствия сессий
--------------------------

