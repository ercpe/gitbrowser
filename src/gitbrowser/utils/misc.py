# -*- coding: utf-8 -*-
from gitbrowser.conf import config


def generate_breadcrumb_path(path):
	l = []
	for chunk in path.split('/'):
		if not chunk:
			continue
		l.append(chunk)
		yield '/'.join(l), chunk


def clone_urls(repo, user):
	return config.clone_urls_builder(repo, user)
