# -*- coding: utf-8 -*-
from pkg_resources import parse_requirements

class PkgResourceWrapper(object):
	def __init__(self, req):
		self.requirement = req

	def url(self):
		return "https://pypi.python.org/pypi/%s" % self.requirement.project_name

	def __str__(self):
		return str(self.requirement)

class PythonRequirements(object):
	def parse(self, content):
		return [PkgResourceWrapper(req) for req in parse_requirements(content)]
