# -*- coding: utf-8 -*-
import logging
import os
import datetime
from django.core.cache import get_cache
from django.core.cache.backends.base import InvalidCacheBackendError

import git
from git.objects.tree import Tree
from git.objects.blob import Blob


###
### Monkey patching of git.objects.commit.Commit
###
from git.objects.commit import Commit
from gitdb.exc import BadObject, BadName
import re
from repoze.lru import lru_cache

Commit.message_without_summary = lambda self: self.message[len(self.summary):].strip()
Commit.changes = lambda self: self.parents[0].diff(self, create_patch=True) \
								if self.parents else \
								self.diff(None, create_patch=True)
Commit.authored_datetime = lambda self: datetime.datetime.fromtimestamp(self.authored_date)
Commit.committed_datetime = lambda self: datetime.datetime.fromtimestamp(self.committed_date)


latest_commit_patch = lru_cache(500)(lambda self: self.repo.iter_commits(paths=self.path, max_count=1).next())

###
### Monkey patching of git.objects.blob.Blob
###
ACCEPT_MIMETYPES_LAMBDAS = (
	lambda mt: mt.startswith('text/'),
	lambda mt: mt.startswith('application/xml'),
	lambda mt: mt.startswith('application/x-javascript'),
)
Blob.can_display = lambda self: any((lmbda(self.mime_type) for lmbda in ACCEPT_MIMETYPES_LAMBDAS))
Blob.content = lambda self: self.data_stream.read()
Blob.latest_commit = latest_commit_patch

###
### Monkey patching of git.objects.blob.Truee
###
Tree.latest_commit = latest_commit_patch

try:
	repo_commit_cache = get_cache('repository-commits')
except InvalidCacheBackendError:
	repo_commit_cache = get_cache('default')

class GitRepository(object):

	def __init__(self, fs_path, relative_path):
		self.repo_path = fs_path
		self.name = os.path.basename(fs_path)
		self.clean_name = self.name[:-4] if self.name.endswith('.git') else self.name
		self.path = os.path.dirname(relative_path)
		self.relative_path = relative_path

		self.list_filter_ref = None
		self.list_filter_path = None

		self._repo_obj = None

		self._commit_list = None

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

	@property
	def list_filter_path_items(self):
		def inner():
			l = []
			for chunk in self.list_filter_path.split('/'):
				if not chunk:
					continue
				l.append(chunk)
				yield '/'.join(l), chunk
		return list(inner())

	@property
	def commit_list(self):
		if not self._commit_list:
			self._commit_list = CommitListWrapper(self.repo, self.list_filter_ref, self.list_filter_path)
		return self._commit_list

	@property
	def tags(self):
		return sorted(self.repo.tags, key=lambda x: x.name, reverse=True)

	def archive(self, stream, *args, **kwargs):
		return self.repo.archive(stream, *args, **kwargs)

	def get_config_value(self, section, option, default=None):
		return self.repo_config.get_value(section, option, default)

	def set_list_filter(self, ref, path):
		logging.info("Applying filter: ref=%s, path=%s" % (ref, path))
		self.list_filter_ref = ref
		self.list_filter_path = path.strip('/')

	def items(self):
		try:
			tree = self.repo.tree(self.list_filter_ref)
		except (BadObject, BadName) as bo:
			logging.warning("Got %s - is the repository empty?" % bo)
			return

		if self.list_filter_path:
			subtree = tree[self.list_filter_path]
		else:
			subtree = tree

		if isinstance(subtree, Tree):
			for item in sorted(subtree, key=lambda item: item.type, reverse=True):
				yield item, None #self.get_latest_commit(item)
		else:
			yield subtree, self.get_latest_commit(subtree)

	def get_commit(self, commit_id):
		return self.repo.commit(commit_id)

	def get_latest_commit(self, item):
		# TODO: This should be improved - albeit it seems it's fast as we can get:
		# https://github.com/gitpython-developers/GitPython/issues/240
		cache_key = "latest_commit_%s" % item.hexsha

		latest_commit_hexsha = repo_commit_cache.get(cache_key)
		if latest_commit_hexsha:
			return git.Commit.new(self.repo, latest_commit_hexsha)

		logging.info("Listing commits for %s in %s" % (item.path, self.list_filter_ref))
		latest_commit = self.repo.iter_commits(rev=self.list_filter_ref, paths=item.path, max_count=1).next()
		repo_commit_cache.set(cache_key, latest_commit.hexsha)

		return latest_commit


class CommitListWrapper(object):
	def __init__(self, repo, filter_ref, filter_path):
		self.repo = repo
		self.filter_ref = filter_ref
		self.filter_path = filter_path
		self._iter_slice = None

	def iter_slice(self, start, stop):
		if self._iter_slice is None:
			self._iter_slice = list(
				self.repo.iter_commits(self.filter_ref, paths=self.filter_path, skip=start, max_count=stop-start)
			)
		return self._iter_slice

	def __len__(self):
		cache_key = "count_%s" % self.repo.head.commit.hexsha
		commit_count = repo_commit_cache.get(cache_key)

		if not commit_count:
			commit_count = long(self.repo.git.rev_list(self.repo.head.commit, '--count'))
			repo_commit_cache.set(cache_key, commit_count)

		return commit_count

#
	def __getitem__(self, item):
		logging.info("Wrapper: __getitem__(item=%s)" % item)

		if isinstance(item, int):
			return self.iter_slice(None, None)[item]

		logging.info("Slice for start %s, stop %s, step %s" % (item.start, item.stop, item.step))
		return self.iter_slice(item.start, item.stop)