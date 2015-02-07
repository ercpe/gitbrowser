# -*- coding: utf-8 -*-

import cProfile, pstats, StringIO
import logging
from django import template

register = template.Library()

@register.tag('profile')
def do_profiling(parser, token):
	nodelist = parser.parse(('endprofile',))
	parser.delete_first_token()
	return ProfilingNode(nodelist)

class ProfilingNode(template.Node):

	def __init__(self, nodelist):
		self.nodelist = nodelist

	def render(self, context):
		pr = cProfile.Profile()
		pr.enable()

		output = self.nodelist.render(context)

		pr.disable()
		s = StringIO.StringIO()
		sortby = 'cumulative'
		ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
		ps.print_stats()
		logging.info(s.getvalue())

		return output