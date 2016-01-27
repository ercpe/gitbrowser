# -*- coding: utf-8 -*-
import urlparse

from django.contrib.humanize.templatetags.humanize import naturaltime
from django import template
from django.core.urlresolvers import reverse
from django.template.base import TemplateSyntaxError
from django.template.defaultfilters import date, slugify
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe
from gitbrowser.utils.linking import Autolinker

register = template.Library()

@register.simple_tag
def time_tag(datetime, label=None, itemprop=""):
	if not datetime:
		return ""

	s = '<time datetime="%s" title="%s"%s>%s</time>' % (
			date(datetime, 'c'),
			datetime,
			(' itemprop="%s"' % itemprop) if itemprop else "",
			label or naturaltime(datetime))

	return mark_safe(s)


@register.simple_tag
def author_tag(author, with_avatar=True, avatar_size=16, itemprop=['author']):
	tpl = """<span %(itemprops)s itemscope itemtype="http://schema.org/Person" id="author_%(email_slug)s">
			%(avatar_code)s
			<a href="mailto:%(email)s"><span itemprop="name">%(author)s</span></a><meta itemprop="email" content="%(email)s" /></span>"""

	avatar_code = ""
	if with_avatar:
		avatar_code = '<img src="%(url)s?email=%(email)s&size=%(avatar_size)s" itemprop="image" title="%(author)s" class="avatar-small" />' % {
			'url': reverse('gitbrowser:avatar'),
			'email': author.email,
			'avatar_size': avatar_size,
			'author': author
		}

	markup = tpl % {
		'avatar_code': avatar_code,
		'email': author.email,
		'email_slug': slugify(author.email),
		'author': author.name,
		'itemprops': ('itemprop="%s" ' % ' '.join(itemprop)) if itemprop else '',
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


@register.inclusion_tag('templatetags/clone_url_selector.html')
def clone_url_selector(repository):
	return {
		'urls': repository.clone_urls
	}


@register.simple_tag(takes_context=True)
def autolink(context, message):
	repository = context.get('repository', None)
	return linebreaks(Autolinker().link(message, repository))