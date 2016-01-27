# -*- coding: utf-8 -*-
import re
import shlex


class DataDumperReader(object):
	"""Parser for dump files created by perl's Data::Dumper."""

	def read(self, filename):
		with open(filename, 'r') as f:
			file_content = f.read()
			return self.parse(file_content)

	def parse(self, raw):
		"""Parses the content of `raw` into python data structures (lists, dictionaries, primitives)
		using a mix of regular expressions and the `shlex` module.

		Returns a dictionary"""

		data = raw

		py_data = {}

		while ';' in data:
			m = re.match('(.*?);$', data, re.MULTILINE | re.DOTALL)
			current_data = m.group(1).strip()

			py_data.update([self.parse_block(current_data)])

			data = data[m.end(1) + 1:]

		assert data.strip() == "", 'Leftovers found: %s' % data

		return py_data

	def parse_block(self, block_data):
		"""Parses a single block of markup into a python data structure"""

		lexer = shlex.shlex(block_data, posix=True)
		lexer.quotes = "'"
		lexer.wordchars += '"'
		lexer.escapedquotes = "'"
		return self.parse_structure(lexer)

	def unquote(self, s):
		if len(s or "") <= 2:
			return s

		if s[0] == s[-1] and s[0] == "'":
			return s[1:-1]
		return s

	def parse_structure(self, lexer):
		"""Starts the parsing process for a concrete data structure by looking at the next token.
		Primitives are returned directly, for lists and dicts :func:`parse_dict` or :func:`parse_list`
		are called
		"""
		token = lexer.get_token()

		if token == '%':
			variable_name = lexer.get_token()
			nt = lexer.get_token()
			assert nt == "=", "Expected equal sign; got %s" % nt
			return self.unquote(variable_name), self.parse_dict(lexer)

		if token == '(' or token == '{':
			lexer.push_token(token)
			return self.parse_dict(lexer)

		if token == '[':
			lexer.push_token(token)
			return self.parse_list(lexer)

		if token == '$':
			variable_name = lexer.get_token()
			nt = lexer.get_token()
			assert nt == "=", "Expected equal sign; got %s" % nt
			return variable_name, lexer.get_token()

		return self.unquote(token)

	def parse_dict(self, lexer):
		"""Parses the current structure block into a python dict. Calls :func:`parse_structure` for each
		value in the dictionary"""

		token = lexer.get_token()
		assert token in ('(', '{'), "Expected '(' or '{'; got %s" % token

		d = {}

		for token in lexer:
			if token == ')' or token == '}':
				break
			if token == ',':
				continue

			variable_name = token
			nt = lexer.get_token() + lexer.get_token()
			assert nt == "=>", "Expected '=>'; got %s" % nt
			d[self.unquote(variable_name)] = self.parse_structure(lexer)

		return d

	def parse_list(self, lexer):
		"""Parses the current structure block into a python list. Calls :func:`parse_structure` for each
		value."""

		token = lexer.get_token()
		assert token == '[', "Expected '['; got %s" % token

		l = []

		for token in lexer:
			if token == ']':
				return l
			if token == ',':
				continue

			lexer.push_token(token)
			list_item = self.parse_structure(lexer)
			l.append(list_item)

			nt = lexer.get_token()
			if nt == ']':
				break
			assert nt == ",", "Expected ','; got %s" % nt
		return l
