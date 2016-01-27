# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.views.generic.base import TemplateView, View, ContextMixin
from gitbrowser.conf import config, LIST_STYLE_FLAT, LIST_STYLE_HIERARCHICAL, LIST_STYLE_TREE
from gitbrowser.views.mixins import BreadcrumbMixin, RepositoryMixin


def dev_null(request):
	raise Http404


class ListRepositoriesView(BreadcrumbMixin, TemplateView):

	def get_template_names(self):
		if config.list_style in (LIST_STYLE_FLAT, LIST_STYLE_HIERARCHICAL):
			return ['repository/list.html']
		if config.list_style == LIST_STYLE_TREE:
			return ['repository/list_tree.html']

	def get_context_data(self, **kwargs):
		d = super(ListRepositoriesView, self).get_context_data(**kwargs)

		repositories = config.lister.list(self.request.user, kwargs.get('path', ''),
											flat=config.list_style in (LIST_STYLE_FLAT, LIST_STYLE_TREE))

		if config.list_style in (LIST_STYLE_FLAT, LIST_STYLE_TREE):
			repositories = sorted(repositories, key=lambda x: x.path)

		d['repositories'] = repositories
		d['alternate_content_types'] = [
			('application/json', self.request.build_absolute_uri(reverse('gitbrowser:json')))
		]
		return d


class RepositoryOverviewView(RepositoryMixin, TemplateView):
	template_name = 'repository/overview.html'
	current_tab = 'overview'
