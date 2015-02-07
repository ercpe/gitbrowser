# -*- coding: utf-8 -*-
from django.core.cache import get_cache
from django.core.cache.backends.base import InvalidCacheBackendError


def gitbrowser_cache(name, keyprefix=''):

	def gen_cache_key(key, config_prefix, version):
		return ':'.join([config_prefix, keyprefix, str(version), key])

	cache = None
	try:
		cache = get_cache(name, **{
			'KEY_FUNCTION': gen_cache_key
		})
	except InvalidCacheBackendError:
		cache = get_cache('default', **{
			'KEY_FUNCTION': gen_cache_key
		})
	return cache