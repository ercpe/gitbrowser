# -*- coding: utf-8 -*-
import json
import logging
from django.http import Http404, HttpResponse
from gitbrowser.conf import config
from gitbrowser.utils.http import bestof
from gitbrowser.utils.misc import generate_breadcrumb_path


class GitbrowserMixin(object):

	def get_context_data(self, **kwargs):
		ctx = super(GitbrowserMixin, self).get_context_data(**kwargs)

		ctx['extra_scripts'] = config.extra_scripts
		ctx['extra_html'] = config.extra_html

		return ctx


class BreadcrumbMixin(GitbrowserMixin):

	def get_context_data(self, **kwargs):
		ctx = super(BreadcrumbMixin, self).get_context_data(**kwargs)

		all_kwargs = self.kwargs
		all_kwargs.update(kwargs)

		if 'path' in all_kwargs:
			ctx['browse_path'] = all_kwargs['path']
			ctx['browse_path_items'] = generate_breadcrumb_path(all_kwargs['path'])

		return ctx


class RepositoryMixin(BreadcrumbMixin):
	current_tab = None
	can_switch_branches = False

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
		ctx['can_switch_branches'] = getattr(self, 'can_switch_branches', False)
		return ctx


class JSONContentNegotiationMixin(object):

	def render_to_response(self, context, **response_kwargs):
		best_content_type = bestof(self.request.META['HTTP_ACCEPT'], 'text/html', 'application/json')

		if best_content_type == 'application/json':
			return self.get_json_response(self.convert_context_to_json(context))
		else:
			context['alternate_content_types'] = [
				('application/json', self.request.build_absolute_uri(self.request.get_full_path()))
			]
			return super(JSONContentNegotiationMixin, self).render_to_response(context, **response_kwargs)

	def get_json_response(self, content, **httpresponse_kwargs):
		return HttpResponse(content, content_type='application/json', **httpresponse_kwargs)

	def convert_context_to_json(self, context):
		return json.dumps(context)