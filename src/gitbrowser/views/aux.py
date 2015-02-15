# -*- coding: utf-8 -*-
import hashlib
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic.base import View
import pydenticon
from pygments.formatters.html import HtmlFormatter
from gitbrowser.conf import config


def styles(request):
	return HttpResponse(HtmlFormatter().get_style_defs('.highlight'), content_type='text/css')


class ContributerAvatarView(View):

	def get(self, request, *args, **kwargs):
		email = request.GET['email']
		size = int(request.GET.get('size', 64))

		if config.feature_enabled('gravatar'):
			md5 = hashlib.md5()
			md5.update(email)
			url = "https://www.gravatar.com/avatar/%s?s=%s" % (md5.hexdigest(), size)
			return HttpResponseRedirect(url)
		else:
			# Set-up a list of foreground colours (taken from Sigil).
			foreground = [
							"rgb(45,79,255)",
							"rgb(254,180,44)",
							"rgb(226,121,234)",
							"rgb(30,179,253)",
							"rgb(232,77,65)",
							"rgb(49,203,115)",
							"rgb(141,69,170)"
			]

			generator = pydenticon.Generator(5, 5, digest=hashlib.sha1,
												foreground=foreground)
			identicon = generator.generate(email, size, size)
			response = HttpResponse(identicon, content_type='image/png')
			return response

	@method_decorator(cache_page(24 * 60 * 60))
	def dispatch(self, request, *args, **kwargs):
		return super(ContributerAvatarView, self).dispatch(request, *args, **kwargs)