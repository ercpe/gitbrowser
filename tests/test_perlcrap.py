# -*- coding: utf-8 -*-

from django.test.testcases import SimpleTestCase
from gitbrowser.utils.perlcrap import DataDumperReader


class PerlCrapTestCase(SimpleTestCase):

	def parse_and_assert(self, s, reader=None):
		reader = reader or DataDumperReader()

		obj = reader.parse(s)
		self.assertTrue(isinstance(obj, dict))
		self.assertGreater(len(obj), 0)

		return obj

	def parse_and_assert_hash(self, s, hash_name='my_hash', assert_isinstance=None, reader=None):
		d = self.parse_and_assert(s, reader)

		self.assertEqual(len(d), 1)
		self.assertEqual(list(d)[0], hash_name)

		obj = d[hash_name]
		if assert_isinstance:
			self.assertTrue(isinstance(obj, assert_isinstance))

		return obj

	def test_parse_scalar(self):
		s = "$foobar = 1;"

		d = self.parse_and_assert(s)
		self.assertEqual(len(d), 1)
		self.assertEqual(list(d)[0], 'foobar')
		self.assertEqual(d['foobar'], '1')

	def test_escaped_quotes(self):
		s = r"$foobar = 'foo\'s bar';"

		d = self.parse_and_assert(s)
		self.assertEqual(len(d), 1)
		self.assertEqual(list(d)[0], 'foobar')
		self.assertEqual(d['foobar'], "foo's bar")

	def test_invalid_input(self):
		s = "foobar"

		try:
			d = self.parse_and_assert(s)
			self.fail("%s should not parse successfully" % s)
		except AssertionError as ae:
			if not str(ae).startswith('Leftovers found:'):
				self.fail('Wrong AssertionError found')
		except Exception as ex:
			self.fail("A %s should not be raised" % type(ex))

	def test_parse_hash(self):
		s = "%foobar = ();"

		d = self.parse_and_assert_hash(s, 'foobar', dict)
		self.assertEqual(len(d), 0)

	def test_parse_list(self):
		s = """%my_hash = (
					'foobar' => [ 1, 2, 3 ]
				);"""

		d = self.parse_and_assert_hash(s, assert_isinstance=dict)

		self.assertEqual(len(d), 1)
		self.assertEqual(list(d)[0], 'foobar')

		l = d['foobar']
		self.assertTrue(isinstance(l, list))
		self.assertEqual(len(l), 3)
		self.assertEqual(l, ['1', '2', '3'])

	def test_nested_lists(self):
		s = """%my_hash = (
					'foobar' => [ [ 1, 2, 3 ] ]
				);"""

		d = self.parse_and_assert_hash(s, assert_isinstance=dict)

		self.assertEqual(len(d), 1)
		self.assertEqual(list(d)[0], 'foobar')

		l = d['foobar']
		self.assertTrue(isinstance(l, list))
		self.assertEqual(len(l), 1)

		self.assertEqual(l[0], ['1', '2', '3'])

	def test_unquote(self):
		reader = DataDumperReader()

		# too short to contain a leading and a trailing quote
		self.assertEqual(reader.unquote(None), None)
		self.assertEqual(reader.unquote(""), "")
		self.assertEqual(reader.unquote("a"), "a")

		# no quotes
		self.assertEqual(reader.unquote("aaaa"), "aaaa")

		# incomplete or wrong quote position
		self.assertEqual(reader.unquote("'aa"), "'aa")
		self.assertEqual(reader.unquote("a'a"), "a'a")
		self.assertEqual(reader.unquote("aa'"), "aa'")

		# wrong quotes (double)
		self.assertEqual(reader.unquote('"a"'), '"a"')

		# quotes at the first and last position
		self.assertEqual(reader.unquote("'aa'"), "aa")

	def test_multi(self):
		s = """$foo = 1;
				$bar = 1;
				$baz = 1;"""

		d = self.parse_and_assert(s)
		self.assertEqual(len(d), 3)
		self.assertEqual(sorted(d.keys()), ['bar', 'baz', 'foo'])

		for x in ['bar', 'baz', 'foo']:
			self.assertEqual(d[x], '1')