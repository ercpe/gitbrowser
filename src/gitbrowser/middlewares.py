# -*- coding: utf-8 -*-
import logging
import re
from django.conf import settings
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


class LoginRequiredMiddleware(object):

	def process_request(self, request):

		exempt_urls = [re.compile(settings.LOGIN_URL.lstrip('/'))]
		if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
			exempt_urls += [re.compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

		path = request.path_info.lstrip('/')
		if not any(m.match(path) for m in exempt_urls):
			if (not config.allow_anonymous) and request.user.is_anonymous():
				return HttpResponseRedirect(settings.LOGIN_URL)
