# -*- coding: utf-8 -*-
import logging
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from gitbrowser.conf import config


class InterceptGitwebMiddleware(object):

	def process_request(self, request):
		if not config.feature_enabled('intercept_gitweb_links'):
			return

		action = request.GET.get('a', None)
		project = request.GET.get('p', None)
		file_or_folder = request.GET.get('f', '')
		head_base = request.GET.get('hb', 'master')
		commit = request.GET.get('h', None)

		if not (project and action):
			return

		redirect_url = None

		if action == "summary":
			redirect_url = reverse('browse', args=(project, ))
		elif action == 'tree':
			redirect_url = reverse('browse_ref', args=(project, head_base, file_or_folder))
		elif action == 'blob':
			redirect_url = reverse('browse_blob', args=(project, head_base, file_or_folder))
		elif action == 'shortlog':
			redirect_url = reverse('commits', args=(project, head_base))
		elif action in ('commit', 'commitdiff', ):
			redirect_url = reverse('commit', args=(project, commit))
		elif action == 'blob_plain':
			#TODO: Implement raw view
			pass

		if redirect_url:
			logging.info("Intercepted gitweb url. Redirecting to %s" % redirect_url)
			return HttpResponseRedirect(redirect_url)

		logging.warning("Could not find a redirect url for p=%s and a=%s" % (project, action))
