# -*- coding: utf-8 -*-
from django.test.testcases import SimpleTestCase
from gitbrowser.utils.http import parse_accept, bestof


class UtilsHTTPTestCase(SimpleTestCase):

	def test_parse_accept(self):
		header = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
		cts = parse_accept(header)

		self.assertEqual(cts, [
			('text/html', 0.9),
			('application/xhtml+xml', 0.9),
			('application/xml', 0.9),
			('image/webp', 0.8),
			('*/*', 0.8)
		])

	def test_parse_accept_no_q(self):
		header = "text/html"
		cts = parse_accept(header)

		self.assertEqual(cts, [
			('text/html', 1.0)
		])

	def test_parse_accept_empty(self):
		self.assertEqual(parse_accept(""), [])

	def test_bestof(self):
		header = "text/html;q=1.0,text/plain;q=0.9,application/xml;q=0.5"
		x = bestof(header, 'text/plain', 'text/html')

		self.assertEqual(x, 'text/html')

	def test_bestof_list(self):
		header = "text/html;q=1.0,text/plain;q=0.9,application/xml;q=0.5"
		x = bestof(header, ['text/plain', 'text/html'])

		self.assertEqual(x, 'text/html')
