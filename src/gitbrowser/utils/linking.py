# -*- coding: utf-8 -*-
import re
from django.core.urlresolvers import reverse
from django.utils.html import format_html, escape
from gitdb.exc import BadName
from six import u

class Autolinker(object):
	# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
	GRUBER_URLINTEXT_PAT = re.compile(u(r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?Â«Â»â€œâ€â€˜â€™]))"""))

	def link(self, raw_text, repository):
		message = escape(raw_text)

		def link_urls(match):
			return format_html('<a href="{0}">{0}</a>', match.group(1))
		message = self.GRUBER_URLINTEXT_PAT.sub(link_urls, message)

		commit_id_re = re.compile(r'(?P<pre_text>(?:(commit|fixes):?\s+))(?P<commit_id>[0-9a-f]{7,42})\b', re.IGNORECASE)

		def build_commit_link(match):
			cid = match.group('commit_id')

			try:
				commit = repository.get_commit(cid)
				return format_html('{0}<a href="{1}" title="{2}">{3}</a>',
					match.group('pre_text'),
					reverse('commit', args=(repository.relative_path, commit.hexsha)),
					commit.summary, cid
				)
			except BadName:
				return match.string

		message = commit_id_re.sub(build_commit_link, message)

		return message
