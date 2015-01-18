# -*- coding: utf-8 -*-
from django.conf import settings
from gitbrowser.utils import lister as lister_module
from gitbrowser.utils import acl as acl_module


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

config = GitbrowserConf()