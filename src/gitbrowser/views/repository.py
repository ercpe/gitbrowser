# -*- coding: utf-8 -*-
from gzip import GzipFile
import json
import logging
import urllib
from django.core.urlresolvers import reverse
from django.utils.http import http_date
from django.core.paginator import PageNotAnInteger, Paginator
from django.core.paginator import EmptyPage
from django.http import StreamingHttpResponse, HttpResponse
from django.template.base import Template
from django.template.context import Context
from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView
from gitbrowser.conf import config, COMMIT_LIST_DEFAULT
from gitbrowser.templatetags.gb_tags import time_tag
from gitbrowser.views.mixins import RepositoryMixin, JSONContentNegotiationMixin


class BrowseTreeView(RepositoryMixin, TemplateView):
	template_name = 'repository/browse.html'
	current_tab = 'source'
	can_switch_branches = True


class RepositoryTreeData(RepositoryMixin, View):

	def get(self, request, *args, **kwargs):
		def _inner():
			for item in self.repository.items():
				try:
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
				except Exception as ex:
					logging.exception("Caught exception while fetching latest commit for %s in %s" % (item, self.repository))
		return StreamingHttpResponse(_inner(), content_type='text/event-stream')


class BrowseBlobView(RepositoryMixin, DetailView):
	template_name = 'repository/blob.html'
	context_object_name = 'blob'
	current_tab = 'source'

	def __init__(self, *args, **kwargs):
		super(BrowseBlobView, self).__init__(*args, **kwargs)
		self._repo = None

	def get_object(self, queryset=None):
		return self.repository.items().next()


class RawBlobView(RepositoryMixin, View):
	http_method_names = ['get', 'head']

	def get(self, request, *args, **kwargs):
		obj = self.repository.items().next()

		def _inner():
			stream = obj.data_stream
			buf = stream.read(4096)
			while buf:
				yield buf
				buf = stream.read(4096)

		response = StreamingHttpResponse(_inner(), content_type=obj.mime_type)
		response['Content-Length'] = obj.size
		response['Etag'] = obj.hexsha
		response['Last-Modified'] = http_date(obj.latest_commit().committed_date)
		response['Content-Disposition'] = "attachment; filename=%s" % urllib.quote(obj.name)
		return response


class CommitDetailView(RepositoryMixin, DetailView):
	template_name = 'repository/commit_detail.html'
	context_object_name = 'commit'
	current_tab = 'commits'

	def get_object(self, queryset=None):
		return self.repository.get_commit(self.kwargs['commit_id'])


class RepositoryCommitsListView(JSONContentNegotiationMixin, RepositoryMixin, TemplateView):
	current_tab = 'commits'
	can_switch_branches = True

	def get_template_names(self):
		if config.commit_list_style == COMMIT_LIST_DEFAULT:
			return ['repository/commits.html']
		else:
			return ['repository/commits_condensed.html']

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

	def convert_context_to_json(self, context):
		def _aa():
			for commit in context['commits']:
				try:
					yield {
						'summary': commit.summary,
						'link': self.request.build_absolute_uri(reverse('commit', args=(
							self.repository.relative_path,
							commit.hexsha
						))),
						'id': commit.hexsha,
						'timestamp': commit.committed_date,
						'committer_name': commit.committer.name,
						'committer_email': commit.committer.email
					}
				except Exception as ex:
					logging.exception("Failed to convert %s" % commit)
		return json.dumps(list(_aa()))


class RepositoryTagsView(JSONContentNegotiationMixin, RepositoryMixin, TemplateView):
	template_name = 'repository/tags.html'
	current_tab = 'tags'

	def convert_context_to_json(self, context):
		def _aa():
			for x in self.repository.tags:
				try:
					yield {
						'name': x.name,
						'archive': self.request.build_absolute_uri(reverse('archive', args=(
							self.repository.relative_path,
							x.name,
							'gz'
						))),
						'timestamp': x.commit.committed_date,
						'description': x.commit.summary
					}
				except Exception as ex:
					logging.exception("Failed to convert %s" % x)
		return json.dumps(list(_aa()))


class RepositoryArchiveView(RepositoryMixin, View):

	def get(self, *args, **kwargs):
		tag = kwargs.get('tag')
		tag_obj = self.repository.get_tag(tag)
		format = kwargs.get('format')

		filename = '%s-%s.tar.%s' % (self.repository.clean_name, tag, format)

		resp = HttpResponse(content_type='application/x-gtar')
		resp['Content-Disposition'] = 'attachment; filename=%s' % filename

		# it's important to set the mtime on the gzip file. Otherwise the current timestamp
		# will be used by GzipFile which will break checksums
		with GzipFile(filename=filename, fileobj=resp, mode='wb',
						compresslevel=5, mtime=tag_obj.commit.committed_date) as gz:
			self.repository.archive(gz, treeish=tag, prefix="%s-%s/" % (self.repository.clean_name, tag))

		return resp