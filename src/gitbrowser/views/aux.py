# -*- coding: utf-8 -*-
import hashlib
from django.http.response import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View
from pygments.formatters.html import HtmlFormatter
from gitbrowser.conf import config


def styles(request):
	return HttpResponse(HtmlFormatter().get_style_defs('.highlight'), content_type='text/css')


class ContributerAvatarView(View):
	def get(self, request, *args, **kwargs):
		if config.feature_enabled('gravatar'):
			# https://www.gravatar.com/avatar/ec420bf66201d17d79f5904b5f3e86e3?s=16
			md5 = hashlib.md5()
			md5.update(request.GET['email'])
			size = request.GET.get('size', 64)
			url = "https://www.gravatar.com/avatar/%s?s=%s" % (md5.hexdigest(), size)
			return HttpResponseRedirect(url)