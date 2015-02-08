# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser
from django.contrib.sitemaps import Sitemap
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.utils.feedgenerator import Atom1Feed
from django.utils.safestring import mark_safe
from gitbrowser.conf import config
from gitbrowser.utils.linking import Autolinker


class RepositorySitemap(Sitemap):

	def items(self):
		return list(config.lister.list(AnonymousUser(), flat=True))

	def location(self, obj):
		return reverse('overview', args=(obj.relative_path, ))

	def lastmod(self, obj):
		return obj.commit_list[0].committed_datetime


class GitbrowserFeed(Feed):
	feed_type = Atom1Feed

	def __init__(self, *args, **kwargs):
		super(GitbrowserFeed, self).__init__(*args, **kwargs)
		self._obj = None

	def get_object(self, request, *args, **kwargs):
		repositories = list(config.lister.list(AnonymousUser(), path=kwargs['path']))
		if not repositories:
			raise Http404

		if len(repositories) > 1:
			raise Exception("more than one repository found for %s" % kwargs['path'])

		self._obj = repositories[0]
		return self._obj


class CommitsFeed(GitbrowserFeed):

	def title(self, obj):
		return self.description(obj)

	def description(self, obj):
		return "Commits in %s" % obj.name

	def link(self, obj):
		return reverse('overview', args=(obj.relative_path, ))

	def items(self, obj):
		return obj.commit_list

	def item_link(self, item):
		return reverse('commit', args=(self._obj.relative_path, item.hexsha, ))

	def item_guid(self, item):
		return item.hexsha

	def item_guid_is_permalink(self, item):
		return False

	def item_author_name(self, item):
		return item.committer.name

	def item_author_email(self, item):
		return item.committer.email

	def item_title(self, item):
		return "[%s] %s" % (item.shorthexsha(), item.summary)

	def item_pubdate(self, item):
		return item.committed_datetime()

	def item_description(self, item):
		return mark_safe(Autolinker().link(item.message, self._obj))
