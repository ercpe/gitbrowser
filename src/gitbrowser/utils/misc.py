# -*- coding: utf-8 -*-

def generate_breadcrumb_path(path):
	l = []
	for chunk in path.split('/'):
		if not chunk:
			continue
		l.append(chunk)
		yield '/'.join(l), chunk
