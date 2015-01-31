# -*- coding: utf-8 -*-
import logging
from django.conf import settings


FEATURE_DEFAULTS = {
	'gravatar': True,
	'render_readme': True,
	'intercept_gitweb_links': True
}

CONFIG_DEFAULTS = {
	'lister': 'GitoliteProjectsFileRepositoryLister',
	'acl': 'AllowAllACL',

	'display': {
		'list_style': 'flat',
	},

	'features': FEATURE_DEFAULTS,

	'clone_url_templates': ['ssh://git@YOUR-SERVER-NAME/%(path)s'],
}


class GitbrowserConf(object):

	def __init__(self):
		self.config_dict = None

	@property
	def gbconf(self):
		if not self.config_dict:
			self.config_dict = CONFIG_DEFAULTS
			self.config_dict.update(getattr(settings, 'GITBROWSER', {}))
			print(self.config_dict)
		return self.config_dict

	@property
	def lister(self):
		from gitbrowser.utils import lister as lister_module
		lister_class_name = self.gbconf.get('lister', 'GitoliteProjectsFileRepositoryLister')
		lister_class = getattr(lister_module, lister_class_name)
		return lister_class(self.acl)

	@property
	def acl(self):
		from gitbrowser.utils import acl as acl_module
		acl_class = self.gbconf.get('acl', 'DenyAllACL')
		return getattr(acl_module, acl_class)()

	@property
	def clone_url_templates(self):
		return self.gbconf.get('clone_url_templates', [])

	@property
	def list_flat(self):
		cfg_value = self.gbconf.get('display', {}).get('list_style', 'flat')
		assert cfg_value in ('flat', 'hierarchical'), 'list_style must be one of "flat",  "hierarchical"'
		return cfg_value == 'flat'

	def feature_enabled(self, feature_name):
		features = FEATURE_DEFAULTS
		features.update(self.gbconf.get('features', {}))
		return features.get(feature_name, False) is True


config = GitbrowserConf()