# -*- coding: utf-8 -*-
import logging

from django import template
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_for_mimetype, get_lexer_for_filename
from pygments.util import ClassNotFound

register = template.Library()

@register.simple_tag(name='highlight')
def pygments_highlight2(code, mime_type, filename=None):
	if not code:
		return ""

	lexer = None

	if mime_type == "text/plain" and filename:
		try:
			lexer = get_lexer_for_filename(filename)
		except ClassNotFound as cnf:
			logging.info("No lexer: %s" % cnf)

	if not lexer:
		lexer = get_lexer_for_mimetype(mime_type)

	return highlight(code, lexer, HtmlFormatter())
