# -*- coding: utf-8 -*-

from django import template
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_for_mimetype

register = template.Library()

@register.filter(name='highlight')
def pygments_highlight(code, mime_type):
	lexer = get_lexer_for_mimetype(mime_type)
	if code:
		return highlight(code, lexer, HtmlFormatter())
	else:
		return ""