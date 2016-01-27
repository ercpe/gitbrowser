# -*- coding: utf-8 -*-
import logging
import re
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect, Http404, HttpResponsePermanentRedirect
from gitbrowser.conf import config


class InterceptGitwebMiddleware(object):
	"""Django Middleware to intercept gitweb-like URLs and issue a redirect
	to real gitbrowser urls"""

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
			redirect_url = reverse('gitbrowser:overview', args=(project, ))
		elif action == 'tree':
			redirect_url = reverse('gitbrowser:browse_ref', args=(project, head_base, file_or_folder))
		elif action == 'blob':
			redirect_url = reverse('gitbrowser:browse_blob', args=(project, head_base, file_or_folder))
		elif action == 'shortlog':
			redirect_url = reverse('gitbrowser:commits', args=(project, head_base))
		elif action in ('commit', 'commitdiff', ):
			redirect_url = reverse('gitbrowser:commit', args=(project, commit))
		elif action == 'blob_plain':
			redirect_url = reverse('gitbrowser:raw', args=(project, head_base, file_or_folder))
		elif action == "history":
			redirect_url = reverse('gitbrowser:history', args=(project, head_base, file_or_folder))
		elif action == "atom" or action == "rss":
			redirect_url = reverse('gitbrowser:feed', args=(project, ))

		if redirect_url:
			logging.info("Intercepted gitweb url. Redirecting to %s" % redirect_url)
			return HttpResponsePermanentRedirect(redirect_url)

		logging.warning("Could not find a redirect url for p=%s and a=%s" % (project, action))
		raise Http404


class LoginRequiredMiddleware(object):

	def process_request(self, request):

		exempt_urls = [re.compile(settings.LOGIN_URL.lstrip('/'))]
		if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
			exempt_urls += [re.compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]

		path = request.path_info.lstrip('/')
		if not any(m.match(path) for m in exempt_urls):
			if (not config.allow_anonymous) and request.user.is_anonymous():
				return HttpResponseRedirect(settings.LOGIN_URL)


class ContentSecurityPolicyMiddleware(object):

	def process_response(self, request, response):
		my_url = request.build_absolute_uri('/')

		csp_urls = {
			'script-src': [my_url],
			'img-src': ["'self'", 'data:', my_url, "*.gravatar.com", "*"],
			'style-src': ['self', "'unsafe-inline'", my_url],
			'connect-src': [my_url],
			'font-src': [my_url],
		}

		conf_urls = getattr(settings, 'CONTENT_SECURITY_POLICY_URLS', None)

		if conf_urls:
			if isinstance(conf_urls, (list, tuple)):
				# one iterable of strings: add them to each key
				for k in csp_urls.keys():
					csp_urls[k].extend(conf_urls)
			elif isinstance(conf_urls, dict):
				# merge dicts
				for conf_k in conf_urls.keys():
					if conf_k not in csp_urls:
						continue
					urls = conf_urls[conf_k] if isinstance(conf_urls[conf_k], (list, tuple)) else [conf_urls[conf_k]]
					csp_urls[conf_k].extend(urls)
			else:
				# consider it a string
				for k in csp_urls.keys():
					csp_urls[k].append(conf_urls)

		response['Content-Security-Policy'] = '; '.join(["%s %s" % (k, ' '.join(v)) for k, v in csp_urls.items()])
		return response
