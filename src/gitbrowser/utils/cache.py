# -*- coding: utf-8 -*-
from django.core.cache import caches
from django.core.cache.backends.base import InvalidCacheBackendError

g_keyprefix=''

def gen_cache_key(key, config_prefix, version):
	global g_keyprefix
	return ':'.join([config_prefix, g_keyprefix, str(version), key])

def gitbrowser_cache(name, keyprefix=''):
	global g_keyprefix

	g_keyprefix = keyprefix

	cache = None
	try:
		cache = caches[name]
	except InvalidCacheBackendError:
		cache = caches['default']
	return cache
