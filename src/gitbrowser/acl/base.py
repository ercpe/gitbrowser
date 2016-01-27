# -*- coding: utf-8 -*-
import logging
from django.core.cache import InvalidCacheBackendError, caches

try:
	acl_cache = caches['acl-cache']
except InvalidCacheBackendError:
	acl_cache = caches['default']


class ACL(object):
	def can_read(self, user, repo):
		raise NotImplementedError


class DenyAllACL(ACL):
	def can_read(self, user, repo):
		logging.info("Access DENIED for %s to %s" % (user, repo))
		return False


class AllowAllACL(ACL):
	def can_read(self, user, repo):
		logging.info("Access GRANTED for %s to %s" % (user, repo))
		return True
