# -*- coding: utf-8 -*-
import json
from django.contrib.auth.models import AnonymousUser
from django.contrib.sitemaps import Sitemap
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.http.response import Http404, HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.feedgenerator import Atom1Feed
from django.views.decorators.cache import cache_page
from django.views.generic import View
from pygments.formatters.html import HtmlFormatter
from gitbrowser.conf import config
import xml.etree.cElementTree as et

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
		return render_to_string('feeds/commit.html', {
			'styles': HtmlFormatter().get_style_defs('.highlight'),
			'commit': item
		})


class RobotsTxtView(View):

	def get(self, request):
		content = "User-agent: *\nDisallow: /accounts/"

		if config.allow_anonymous:
			content += """
Allow: /
Sitemap: %s""" % request.build_absolute_uri(reverse('sitemap'))
		else:
			content += "Disallow: /"

		return HttpResponse(content, content_type='text/plain')


class OPMLView(View):
	@method_decorator(cache_page(15 * 60 * 60))
	def dispatch(self, request, *args, **kwargs):
		return super(OPMLView, self).dispatch(request, *args, **kwargs)

	def get(self, request):

		opml = et.Element("opml")
		opml.attrib['version'] = '1.0'

		head = et.SubElement(opml, 'head')
		et.SubElement(head, 'title').text = 'Git Repositories'

		body = et.SubElement(opml, 'body')
		outline = et.SubElement(body, 'outline')
		outline.attrib['text'] = 'RSS feeds'

		for repository in config.lister.list(request.user, flat=True):
			x = et.SubElement(outline, 'outline')
			x.attrib['type'] = 'rss'
			x.attrib['text'] = repository.name
			x.attrib['title'] = repository.name
			x.attrib['xmlUrl'] = request.build_absolute_uri(reverse('feed', args=(repository.relative_path, )))
			x.attrib['htmlUrl'] = request.build_absolute_uri(reverse('overview', args=(repository.relative_path, )))

		tree = et.ElementTree(opml)
		response = HttpResponse(content_type='application/xml')
		tree.write(response)
		return response


class JSONView(View):

	@method_decorator(cache_page(15 * 60 * 60))
	def dispatch(self, request, *args, **kwargs):
		return super(JSONView, self).dispatch(request, *args, **kwargs)

	def get(self, request):
		l = [{
				'title': repo.relative_path,
				'description': repo.description,
				'html': request.build_absolute_uri(reverse('overview', args=(repo.relative_path, ))),
				'code': repo.preferred_clone_url,
				'feed': request.build_absolute_uri(reverse('feed', args=(repo.relative_path, ))),
				'readme': request.build_absolute_uri(reverse('raw', args=(
					repo.relative_path, repo.current_branch, repo.readme_item
				))) if repo.readme_item else None,
				'tags': request.build_absolute_uri(reverse('tags', args=(repo.relative_path, ))) if repo.tags else None,
				'commits': request.build_absolute_uri(reverse('commits', args=(repo.relative_path, repo.current_branch)))
			} for repo in config.lister.list(request.user, flat=True)
		]
		return HttpResponse(json.dumps(l), content_type='application/json')