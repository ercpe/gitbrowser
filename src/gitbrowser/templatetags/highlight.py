# -*- coding: utf-8 -*-

from django import template
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_for_mimetype, get_lexer_for_filename

register = template.Library()


@register.simple_tag(name='highlight')
def pygments_highlight2(code, mime_type, filename=None):
	if not code:
		return ""

	if mime_type == "text/plain" and filename:
		lexer = get_lexer_for_filename(filename)
	else:
		lexer = get_lexer_for_mimetype(mime_type)

	return highlight(code, lexer, HtmlFormatter())
