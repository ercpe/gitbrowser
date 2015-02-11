# -*- coding: utf-8 -*-
import bleach
from django.utils.html import linebreaks
from docutils.core import publish_parts
import markdown
from markdown.extensions.headerid import HeaderIdExtension


class Renderer(object):

	def render(self, markup):
		raise NotImplementedError


class PlainTextRenderer(Renderer):

	def render(self, markup):
		return linebreaks(markup)


class MarkdownRenderer(Renderer):

	def render(self, markup):
		extensions = [
			HeaderIdExtension([]),
		]

		md = markdown.Markdown(extensions, output_format='html5')
		return md.convert(bleach.clean(markup))


class RestructuredTextRenderer(Renderer):

	def render(self, markup):
		return publish_parts(bleach.clean(markup), writer_name='html')['html_body']


def get_renderer_by_name(name, fallback_renderer_name='text'):
	if name == 'text':
		return PlainTextRenderer()
	if name == 'markdown':
		return MarkdownRenderer()
	if name == 'rest':
		return RestructuredTextRenderer()

	if fallback_renderer_name:
		return get_renderer_by_name(fallback_renderer_name, None)