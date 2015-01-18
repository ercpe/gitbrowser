# -*- coding: utf-8 -*-
import logging
from django.http.response import Http404
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from gitbrowser.conf import config


class ListRepositoriesView(TemplateView):
	template_name = 'repo_list.html'

	def get_context_data(self, **kwargs):
		d = super(ListRepositoriesView, self).get_context_data()
		d['repositories'] = lambda: config.lister.get_repositories(self.request.user)
		return d


class TreeOperationMixin(object):

	def __init__(self, *args, **kwargs):
		self._repo = None

	@property
	def repository(self):
		if not self._repo:
			repo = config.lister.get_repository(self.request.user, self.kwargs['path'])
			if not repo:
				raise Http404

			repo_ref = self.kwargs.get('ref', 'master')
			repo_path = self.kwargs.get('repo_path', '')

			repo.set_list_filter(repo_ref, repo_path)

			self._repo = repo
		return self._repo


class BrowseTreeView(TreeOperationMixin, DetailView):
	template_name = 'repo_browse.html'
	context_object_name = 'repository'

	def get_object(self, queryset=None):
		return self.repository


class BrowseBlobView(TreeOperationMixin, DetailView):
	template_name = 'repo_blob.html'
	context_object_name = 'blob'

	def __init__(self, *args, **kwargs):
		super(BrowseBlobView, self).__init__(*args, **kwargs)
		self._repo = None

	def get_object(self, queryset=None):
		return self.repository.items().next()[0]

	def get_context_data(self, **kwargs):
		return super(BrowseBlobView, self).get_context_data(repository=self.repository)


class CommitDetailView(TreeOperationMixin, DetailView):
	template_name = 'commit_detail.html'
	context_object_name = 'commit'

	def get_object(self, queryset=None):
		return self.repository.get_commit(self.kwargs['commit_id'])

	def get_context_data(self, **kwargs):
		return super(CommitDetailView, self).get_context_data(repository=self.repository)