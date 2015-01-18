# -*- coding: utf-8 -*-
import logging
import os

import git
from git.objects.tree import Tree
from git.objects.blob import Blob


###
### Monkey patching of git.objects.commit.Commit
###
def message_without_summary(self):
	return self.message[len(self.summary):]

def changes(self):
	return self.parents[0].diff(self, create_patch=True)

from git.objects.commit import Commit
Commit.message_without_summary = message_without_summary
Commit.changes = changes


###
### Monkey patching of git.objects.blob.Blob
###

ACCEPT_MIMETYPES_LAMBDAS = (
	lambda mt: mt.startswith('text/'),
	lambda mt: mt.startswith('application/xml'),
)

Blob.can_display = lambda self: any((lmbda(self.mime_type) for lmbda in ACCEPT_MIMETYPES_LAMBDAS)) # self.mime_type in ['text/plain']
Blob.content = lambda self: self.data_stream.read()


class GitRepository(object):

	def __init__(self, fs_path, relative_path):
		self.repo_path = fs_path
		self.name = os.path.basename(fs_path)
		self.path = os.path.dirname(relative_path)
		self.relative_path = relative_path

		self.list_filter_ref = None
		self.list_filter_path = None

		self._repo_obj = None

	def __unicode__(self):
		return self.relative_path

	def __repr__(self):
		return self.relative_path

	@property
	def repo(self):
		if not self._repo_obj:
			self._repo_obj = git.Repo(self.repo_path)
		return self._repo_obj

	@property
	def repo_config(self):
		return self.repo.config_reader('repository')

	@property
	def description(self):
		return self.get_config_value('gitweb', 'description', '')

	def get_config_value(self, section, option, default=None):
		return self.repo_config.get_value(section, option, default)

	def set_list_filter(self, ref, path):
		logging.info("Applying filter: ref=%s, path=%s" % (ref, path))
		self.list_filter_ref = ref
		self.list_filter_path = path.strip('/')

	def items(self):
		tree = self.repo.tree(self.list_filter_ref)

		if self.list_filter_path:
			subtree = tree[self.list_filter_path]
		else:
			subtree = tree

		if isinstance(subtree, Tree):
			for item in sorted(subtree, key=lambda item: item.type, reverse=True):
				yield item, self.get_latest_commit(item)
		else:
			yield subtree, self.get_latest_commit(subtree)

	def get_commit(self, commit_id):
		for x in self.repo.iter_commits(rev=commit_id):
			return x

	def get_latest_commit(self, item):
		# TODO: This should be improved - hitting the commits for every item
		# 		in the tree is tooooo slow
		logging.info("Listing commits for %s in %s" % (item.path, self.list_filter_ref))
		return self.repo.iter_commits(rev=self.list_filter_ref, paths=item.path).next()