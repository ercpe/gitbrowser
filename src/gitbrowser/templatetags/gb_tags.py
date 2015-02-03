# -*- coding: utf-8 -*-

from django.contrib.humanize.templatetags.humanize import naturaltime
from django import template
from django.core.urlresolvers import reverse
from django.template.defaultfilters import date, slugify
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

@register.simple_tag
def author_tag(author, with_avatar=True, itemprops=['author']):
	tpl = """<span %(itemprops)s itemscope itemtype="http://schema.org/Person" id="author_%(email_slug)s">
			%(avatar_code)s
			<a href="mailto:%(email)s"><span itemprop="name">%(author)s</span></a><meta itemprop="email" content="%(email)s" /></span>"""

	markup = tpl % {
		'avatar_code': '<img src="%(avatar_url)s" itemprop="image" title="%(author)s" class="avatar-small" />' % {
			'avatar_url': "%s?email=%s&size=16" % (reverse('avatar'), author.email),
			'author': author.name
		} if with_avatar else '',
		'email': author.email,
		'email_slug': slugify(author.email),
		'author': author.name,
		'itemprops': ('itemprop="%s" ' % ' '.join(itemprops)) if itemprops else '',
	}
	return markup
