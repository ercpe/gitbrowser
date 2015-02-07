# -*- coding: utf-8 -*-
import logging
import os
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

LIST_STYLE_FLAT = "flat"
LIST_STYLE_HIERARCHICAL = "hierarchical"
LIST_STYLE_TREE = "tree"

LIST_STYLES = (LIST_STYLE_FLAT, LIST_STYLE_HIERARCHICAL, LIST_STYLE_TREE)

class GitbrowserConf(object):

	def __init__(self):
		self.config_dict = None

	@property
	def gbconf(self):
		if not self.config_dict:
			self.config_dict = CONFIG_DEFAULTS
			self.config_dict.update(getattr(settings, 'GITBROWSER', {}))
		return self.config_dict

	@property
	def lister(self):
		from gitbrowser.utils import lister as lister_module
		lister_class_name = self.gbconf.get('lister', 'GitoliteProjectsFileRepositoryLister')
		lister_class = getattr(lister_module, lister_class_name)
		return lister_class(self.acl)

	@property
	def acl(self):
		from gitbrowser import acl as acl_module
		acl_class = self.gbconf.get('acl', 'DenyAllACL')
		return getattr(acl_module, acl_class)()

	@property
	def clone_url_templates(self):
		return self.gbconf.get('clone_url_templates', [])

	@property
	def clone_urls_builder(self):
		default = '%(path)s'
		value = self.gbconf.get('clone_url_templates', default)

		if isinstance(value, basestring):
			return lambda repo, user=None: [ value % { 'path': repo.relative_path } ]

		assert callable(value), "Expected clone_url_templates to be a string or a callable, got %s" % value
		return value

	@property
	def list_flat(self):
		return self.list_style == LIST_STYLE_FLAT

	@property
	def list_style(self):
		cfg_value = self.gbconf.get('display', {}).get('list_style', 'flat')
		assert cfg_value in LIST_STYLES, 'list_style must be one of %s' % ', '.join(LIST_STYLES)
		return cfg_value

	@property
	def acl_debug(self):
		return self.gbconf.get('debug', {}).get('acl', False) is True

	@property
	def gitolite_home(self):
		return self.get('GL_HOME', os.path.expanduser('~'))

	def feature_enabled(self, feature_name):
		features = FEATURE_DEFAULTS
		features.update(self.gbconf.get('features', {}))
		return features.get(feature_name, False) is True

	def get(self, item, default=None):
		return self.gbconf.get(item, default)


config = GitbrowserConf()