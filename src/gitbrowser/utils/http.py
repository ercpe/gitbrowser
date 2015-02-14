# -*- coding: utf-8 -*-
import re

def parse_accept(accept_header):
	if not accept_header:
		return []

	l = []
	for content_types, q in re.findall("([\w\d/\+,\.\*]+)(?:;q=([\d\.]+),?)?", accept_header):
		for ct in (x.strip() for x in content_types.split(',') if x.strip()):
			q = q or '1.0'
			l.append((ct, float(q)))
	return l

def bestof(accept_header, *args):
	wanted_content_types = []
	for x in args:
		if isinstance(x, (list, tuple)):
			wanted_content_types += list(x)
		else:
			wanted_content_types.append(x)

	accepted_content_types = sorted(parse_accept(accept_header), key=lambda x: x[1], reverse=True)
	for ct, q in accepted_content_types:
		if ct in wanted_content_types:
			return ct

