# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SSOSession'
        db.create_table('sso_session', (
            ('sso_session_key', self.gf('django.db.models.fields.CharField')(max_length=40, primary_key=True)),
            ('django_session_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal('ssosp', ['SSOSession'])


    def backwards(self, orm):
        # Deleting model 'SSOSession'
        db.delete_table('sso_session')


    models = {
        'ssosp.ssosession': {
            'Meta': {'object_name': 'SSOSession', 'db_table': "'sso_session'"},
            'django_session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'sso_session_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'primary_key': 'True'})
        }
    }

    complete_apps = ['ssosp']