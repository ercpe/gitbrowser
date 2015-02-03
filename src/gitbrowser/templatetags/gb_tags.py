# -*- coding: utf-8 -*-

from django.contrib.humanize.templatetags.humanize import naturaltime
from django import template
from django.core.urlresolvers import reverse
from django.template.base import TemplateSyntaxError
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


@register.tag('bootstrap_tab')
def do_bootstrap_tab(parser, token):
	try:
		tag_name, tab_name = token.split_contents()
		if not (tab_name[0] == tab_name[-1] and tab_name[0] in ('"', "'")):
			raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
	except ValueError:
		raise TemplateSyntaxError("%r tag takes exact two parameter" % token.contents.split()[0])

	nodelist = parser.parse(('endbootstrap_tab',))
	parser.delete_first_token()
	return BootstrapTabNode(nodelist, tab_name[1:-1])


class BootstrapTabNode(template.Node):

	def __init__(self, nodelist, tabname):
		self.nodelist = nodelist
		self.tabname = tabname

	def render(self, context):
		output = self.nodelist.render(context)

		css = ' class="active"' if context.get('current_tab', None) == self.tabname else ""
		return '<li role="presentation"%s>' % css + output + '</li>'
