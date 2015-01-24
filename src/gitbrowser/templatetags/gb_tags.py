# -*- coding: utf-8 -*-

from django.contrib.humanize.templatetags.humanize import naturaltime
from django import template
from django.template.defaultfilters import date
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def time_tag(datetime, label=None, autoescape=None):
	if not datetime:
		return ""

	s = '<time datetime="%s" title="%s">%s</time>' % (
			date(datetime, 'c'),
			datetime,
			label or naturaltime(datetime))

	return mark_safe(s)