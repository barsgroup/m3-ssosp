#coding:utf-8


class BaseSSOSessionMap(object):
    def get_django_session_key(self, sso_session_key):
        raise NotImplementedError

    def get_sso_session_key(self, django_session_key):
        raise NotImplementedError

    def exists_sso_session(self, sso_session_key):
        raise NotImplementedError

    def exists_django_session(self, django_session_key):
        raise NotImplementedError

    def set_session_map(self, sso_session_key, django_session_key):
        raise NotImplementedError

    def delete_by_sso_session(self, sso_session_key):
        raise NotImplementedError

    def delete_by_django_session(self, django_session_key):
        raise NotImplementedError