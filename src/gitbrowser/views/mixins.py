# -*- coding: utf-8 -*-
import logging
from django.http import Http404
from gitbrowser.conf import config
from gitbrowser.utils.misc import generate_breadcrumb_path


class BreadcrumbMixin(object):

	def get_context_data(self, **kwargs):
		ctx = super(BreadcrumbMixin, self).get_context_data(**kwargs)

		if 'path' in kwargs:
			ctx['browse_path'] = kwargs['path']
			ctx['browse_path_items'] = generate_breadcrumb_path(kwargs['path'])

		return ctx


class RepositoryMixin(BreadcrumbMixin):
	current_tab = None

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

	def get_context_data(self, **kwargs):
		ctx = super(RepositoryMixin, self).get_context_data(**kwargs)
		ctx['repository'] = self.repository
		ctx['current_tab'] = getattr(self, 'current_tab', None)
		return ctx
