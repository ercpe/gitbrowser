# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser
from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse
from gitbrowser.conf import config


class RepositorySitemap(Sitemap):

	def items(self):
		return list(config.lister.list(AnonymousUser(), flat=True))

	def location(self, obj):
		return reverse('overview', args=(obj.relative_path, ))

	def lastmod(self, obj):
		return obj.commit_list[0].committed_datetime