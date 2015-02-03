# -*- coding: utf-8 -*-
from gzip import GzipFile
import json
import logging
from django.core.paginator import PageNotAnInteger, Paginator
from django.core.paginator import EmptyPage
from django.http.response import Http404, StreamingHttpResponse, HttpResponse
from django.template.base import Template
from django.template.context import Context
from django.views.generic.base import TemplateView, View, ContextMixin
from django.views.generic.detail import DetailView
from gitbrowser.conf import config, LIST_STYLE_FLAT, LIST_STYLE_HIERARCHICAL, LIST_STYLE_TREE
from gitbrowser.templatetags.gb_tags import time_tag
from gitbrowser.views.mixins import BreadcrumbMixin, RepositoryMixin


def dev_null(request):
	raise Http404

class ListRepositoriesView(BreadcrumbMixin, TemplateView):

	def get_template_names(self):
		if config.list_style in (LIST_STYLE_FLAT, LIST_STYLE_HIERARCHICAL):
			return ['repo_list.html']
		if config.list_style == LIST_STYLE_TREE:
			return ['repo_list_tree.html']

	def get_context_data(self, **kwargs):
		d = super(ListRepositoriesView, self).get_context_data(**kwargs)

		repositories = config.lister.list(self.request.user, kwargs.get('path', ''),
											flat=config.list_style in (LIST_STYLE_FLAT, LIST_STYLE_TREE))

		if config.list_style in (LIST_STYLE_FLAT, LIST_STYLE_TREE):
			repositories = sorted(repositories, key=lambda x: x.path)

		d['repositories'] = repositories
		return d


class BrowseTreeView(RepositoryMixin, TemplateView):
	template_name = 'repo_browse.html'
	current_tab = 'source'

class RepositoryTreeData(RepositoryMixin, View):

	def get(self, request, *args, **kwargs):
		def _inner():
			for item in self.repository.items():
				commit = self.repository.get_latest_commit(item)
				yield "data: %s\n\n" % json.dumps({
					'summary_link': Template('''<a class="text-muted"
								href="{% url 'commit' repository.relative_path commit.hexsha %}"
								title="{{commit.summary}}">{{commit.summary}}</a>''').render(Context({
						'repository': self.repository,
						'commit': commit
					})),
					'commit_datetime': time_tag(commit.authored_datetime()),
					'obj': item.hexsha
				})
		return StreamingHttpResponse(_inner(), content_type='text/event-stream')


class BrowseBlobView(RepositoryMixin, DetailView):
	template_name = 'repo_blob.html'
	context_object_name = 'blob'
	current_tab = 'source'

	def __init__(self, *args, **kwargs):
		super(BrowseBlobView, self).__init__(*args, **kwargs)
		self._repo = None

	def get_object(self, queryset=None):
		return self.repository.items().next()


class CommitDetailView(RepositoryMixin, DetailView):
	template_name = 'commit_detail.html'
	context_object_name = 'commit'

	def get_object(self, queryset=None):
		return self.repository.get_commit(self.kwargs['commit_id'])


class RepositoryCommitsListView(RepositoryMixin, TemplateView):
	template_name = 'repo_commits.html'
	current_tab = 'commits'

	def get_context_data(self, **kwargs):
		# TODO: Show error page if the reference does not exist
		d = super(RepositoryCommitsListView, self).get_context_data(**kwargs)

		paginator = Paginator(self.repository.commit_list, 25)

		page = self.request.GET.get('page')
		try:
			commits = paginator.page(page)
		except PageNotAnInteger:
			commits = paginator.page(1)
		except EmptyPage:
			commits = paginator.page(paginator.num_pages)

		d['paginator'] = paginator
		d['commits'] = commits
		return d


class RepositoryTagsView(RepositoryMixin, TemplateView):
	template_name = 'repo_tags.html'
	current_tab = 'tags'


class RepositoryArchiveView(RepositoryMixin, View):

	def get(self, *args, **kwargs):
		tag = kwargs.get('tag')
		format = kwargs.get('format')

		filename = '%s-%s.tar.%s' % (self.repository.clean_name, tag, format)

		resp = HttpResponse(content_type='application/x-gtar')
		resp['Content-Disposition'] = 'attachment; filename=%s' % filename

		with GzipFile(filename=filename, fileobj=resp, mode='wb', compresslevel=5) as gz:
			self.repository.archive(gz, treeish=tag)

		return resp