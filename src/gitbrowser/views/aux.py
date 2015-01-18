# -*- coding: utf-8 -*-
from django.http.response import HttpResponse
from pygments.formatters.html import HtmlFormatter

def styles(request):
	return HttpResponse(HtmlFormatter().get_style_defs('.highlight'), content_type='text/css')
