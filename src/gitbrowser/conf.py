# -*- coding: utf-8 -*-
from django.conf import settings



FEATURE_DEFAULTS = {
	'gravatar': True,
	'render_readme': True,
}


class GitbrowserConf(object):

	@property
	def _gbconf(self):
		return getattr(settings, 'GITBROWSER', {})

	@property
	def lister(self):
		from gitbrowser.utils import lister as lister_module
		lister_class = self._gbconf.get('lister', 'GitoliteProjectsFileRepositoryLister')
		return getattr(lister_module, lister_class)(self.acl)

	@property
	def acl(self):
		from gitbrowser.utils import acl as acl_module
		acl_class = self._gbconf.get('acl', 'DenyAllACL')
		return getattr(acl_module, acl_class)()

	@property
	def clone_url_templates(self):
		return self._gbconf.get('clone_url_templates', [])

	def feature_enabled(self, feature_name):
		features = FEATURE_DEFAULTS
		features.update(self._gbconf.get('features', {}))
		return features.get(feature_name, False) is True


config = GitbrowserConf()