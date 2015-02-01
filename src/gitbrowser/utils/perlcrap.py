# -*- coding: utf-8 -*-
import re
import shlex


class DataDumperReader(object):

	def read(self, filename):
		with open(filename, 'r') as f:
			file_content = f.read()
			return self.parse(file_content)

	def parse(self, raw):
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
		token = lexer.next()

		if token == '%':
			variable_name = lexer.next()
			nt = lexer.next()
			assert nt == "=", "Expected equal sign; got %s" % nt
			return self.unquote(variable_name), self.parse_dict(lexer)

		if token == '(' or token == '{':
			lexer.push_token(token)
			return self.parse_dict(lexer)

		if token == '[':
			lexer.push_token(token)
			return self.parse_list(lexer)

		if token == '$':
			variable_name = lexer.next()
			nt = lexer.next()
			assert nt == "=", "Expected equal sign; got %s" % nt
			return variable_name, lexer.next()

		return self.unquote(token)

	def parse_dict(self, lexer):
		token = lexer.next()
		assert token in ('(', '{'), "Expected '(' or '{'; got %s" % token

		d = {}

		for token in lexer:
			if token == ')' or token == '}':
				break
			if token == ',':
				continue

			variable_name = token
			nt = lexer.next() + lexer.next()
			assert nt == "=>", "Expected '=>'; got %s" % nt
			d[self.unquote(variable_name)] = self.parse_structure(lexer)

		return d

	def parse_list(self, lexer):
		token = lexer.next()
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

			nt = lexer.next()
			if nt == ']':
				break
			assert nt == ",", "Expected ','; got %s" % nt
		return l
