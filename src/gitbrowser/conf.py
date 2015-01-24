# -*- coding: utf-8 -*-
from django.conf import settings
from gitbrowser.utils import lister as lister_module
from gitbrowser.utils import acl as acl_module


FEATURE_DEFAULTS = {
	'gravatar': True,
}


class GitbrowserConf(object):

	@property
	def _gbconf(self):
		return getattr(settings, 'GITBROWSER', {})

	@property
	def lister(self):
		lister_class = self._gbconf.get('lister', 'GitoliteProjectsFileRepositoryLister')
		return getattr(lister_module, lister_class)(self.acl)

	@property
	def acl(self):
		acl_class = self._gbconf.get('acl', 'DenyAllACL')
		return getattr(acl_module, acl_class)()

	def feature_enabled(self, feature_name):
		features = self._gbconf.get('features', {})
		return features.get(feature_name, FEATURE_DEFAULTS[feature_name]) == True


config = GitbrowserConf()