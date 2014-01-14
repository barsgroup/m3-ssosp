.. ssosp documentation master file, created by
   sphinx-quickstart on Fri Jan 10 17:04:06 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SSOSP - Single Sign-On Service Provider
=======================================

SSO - `Технология единого входа`_ в комплекс приложений (`Single Sign-On`_)
может реализовываться различными способами. Один из них - спецификация `SAML 2.0`_.

За основу была взята реализация [1_] сервис провайдера SAML 2 для Django
(которая в свою очередь является наследником другой реализации [2_]).


.. _Технология единого входа: http://ru.wikipedia.org/wiki/%D0%A2%D0%B5%D1%85%D0%BD%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%8F_%D0%B5%D0%B4%D0%B8%D0%BD%D0%BE%D0%B3%D0%BE_%D0%B2%D1%85%D0%BE%D0%B4%D0%B0
.. _Single Sign-On: http://en.wikipedia.org/wiki/Single_sign-on
.. _SAML 2.0: https://docs.google.com/document/d/1l7yDf87qYXQZyJpiiSwH0fKjv7XJNyz9GtftixjpbI4/view
.. _1: https://github.com/easel/django-saml2-sp
.. _2: https://code.google.com/p/django-saml2-sp/

Содержание:

.. toctree::
   :maxdepth: 2

   overview
   install
   basic


..  Дополнительно
    -------------

    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`

