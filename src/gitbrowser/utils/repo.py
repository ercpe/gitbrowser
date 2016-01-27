# -*- coding: utf-8 -*-
import logging
import os
import datetime
import traceback
import urlparse
import git
from git.objects.tree import Tree
from git.objects.blob import Blob
from git.objects.commit import Commit
from gitdb.exc import BadObject, BadName
from natsort import versorted
from pkg_resources import RequirementParseError

from gitbrowser.conf import config
from gitbrowser.utils.cache import gitbrowser_cache
from gitbrowser.utils.deps import PythonRequirements
from gitbrowser.utils.misc import generate_breadcrumb_path
from gitbrowser.utils.rendering import get_renderer_by_name


# Cache that holds the hexsha of commits for blobs
repo_commit_cache = gitbrowser_cache('repository-commits', 'latest_commit_')

# Cache that holds the hexsha of commits and the paths (e.g. refs/tags/1.0) of the tag
tag_commit_cache = gitbrowser_cache('tag-commit', 'tc')

# Cache that holds the total number of commits in a repository
repo_commit_count_cache = gitbrowser_cache('repository-commit-count', 'count')


README_CHOICES = [
	('README.md', 'markdown',),
	('README.rst', 'rest'),
	('README', 'text'),
	('README.txt', 'text'),
]

DEPENDENCY_CHOICES = (
	('requirements.txt', PythonRequirements),
)

###
### Monkey patching of git.objects.commit.Commit
###

def changes(self):
	if self.parents:
		for x in self.parents[0].diff(self, create_patch=True):
			yield x
	else:
		tree = self.tree
		for item in tree:
			if not isinstance(item, Blob):
				continue

			yield {
				'a_blob': { 'path': item.path },
				'diff': item.data_stream.read()
			}


Commit.message_without_summary = lambda self: self.message[len(self.summary):].strip()
Commit.changes = changes
Commit.authored_datetime = lambda self: datetime.datetime.fromtimestamp(self.authored_date)
Commit.committed_datetime = lambda self: datetime.datetime.fromtimestamp(self.committed_date)
Commit.stats_iter = lambda self: ((k, self.stats.files[k]['insertions'], self.stats.files[k]['deletions']) for k in sorted(self.stats.files.keys()))
Commit.shorthexsha = lambda self: self.hexsha[:7]

def tag_for_commit(self):
	tags = tag_commit_cache.get(self.repo.head.commit.hexsha)

	if not tags:
		tags = dict([(x.commit.hexsha, x.path) for x in self.repo.tags])
		tag_commit_cache.set(self.repo.head.commit.hexsha, tags)

	for _t in self.repo.tags:
		if self.hexsha == _t.commit:
			return self.repo.tag(tags[self.hexsha])

Commit.tag = tag_for_commit


def latest_commit_patch(self):
	latest_commit_hexsha = repo_commit_cache.get(self.hexsha)
	if latest_commit_hexsha:
		logging.debug("Cache HIT for %s" % self.hexsha)
		return git.Commit.new(self.repo, latest_commit_hexsha)

	latest_commit = self.repo.iter_commits(paths=self.path, max_count=1).next()
	repo_commit_cache.set(self.hexsha, latest_commit.hexsha)
	return latest_commit

###
### Monkey patching of git.objects.blob.Blob
###
ACCEPT_MIMETYPES_LAMBDAS = (
	lambda mt: mt.startswith('text/'),
	lambda mt: mt.startswith('application/xml'),
	lambda mt: mt.startswith('application/x-javascript'),
	lambda mt: mt.startswith('application/x-sql'),
)
Blob.can_display = lambda self: any((lmbda(self.mime_type) for lmbda in ACCEPT_MIMETYPES_LAMBDAS))
Blob.content = lambda self: self.data_stream.read()
Blob.latest_commit = latest_commit_patch

###
### Monkey patching of git.objects.blob.Truee
###
Tree.latest_commit = latest_commit_patch

def clean_path(s):
	return s[:-4] if s.endswith('.git') else s

class GitRepository(object):

	def __init__(self, fs_path, relative_path, user=None):
		self.repo_path = fs_path
		self.name = os.path.basename(fs_path)

		self.path = os.path.dirname(relative_path)
		self.relative_path = relative_path

		self.list_filter_ref = None
		self.list_filter_path = None

		self._repo_obj = None

		self._commit_list = None
		self.user = user

	def __unicode__(self):
		return self.relative_path

	def __repr__(self):
		return self.relative_path

	@property
	def clean_path(self):
		return clean_path(self.repo_path)

	@property
	def clean_name(self):
		return clean_path(self.name)

	@property
	def clean_relative_path(self):
		return clean_path(self.relative_path)

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
	def last_update(self):
		if self.commit_list:
			return self.commit_list[0].committed_datetime

	@property
	def list_filter_path_items(self):
		"""
		:return: a list of tuples (relative path, label) for all items in list_filter_path
		"""
		return list(generate_breadcrumb_path(self.list_filter_path))

	@property
	def commit_list(self):
		if not self._commit_list:
			self._commit_list = CommitListWrapper(self.repo, self.list_filter_ref, self.list_filter_path)
		return self._commit_list

	def get_tag(self, name):
		return self.repo.tag('refs/tags/%s' % name)

	@property
	def tags(self):
		return versorted(self.repo.tags, key=lambda x: x.name, reverse=True)

	@property
	def branches(self):
		return self.repo.branches

	@property
	def current_branch(self):
		return self.repo.active_branch

	@property
	def list_filter_root(self):
		""":return bool True if the current list filter points to the root of the repository"""
		return self.list_filter_path.rstrip('/') == ""

	@property
	def preferred_clone_url(self):
		urls = self.clone_urls
		if urls:
			return urls[0][1]

	@property
	def clone_urls(self):
		return [
			(urlparse.urlsplit(url).scheme.upper(), url) for url in \
				config.clone_urls_builder(self, self.user.username if self.user else None)
		]

	@property
	def readme(self):
		if not config.feature_enabled('render_readme'):
			return

		for filename, renderer_name in README_CHOICES:
			try:
				items = list(self.items(filename))
			except KeyError:
				continue

			if len(items or []) == 1 and isinstance(items[0], Blob):
				logging.info("Found readme %s" % filename)
				try:
					renderer = get_renderer_by_name(renderer_name)
					return renderer.render(items[0].content())
				except Exception as ex:
					logging.error("Could not render readme %s - %s" % (filename, ex))
					logging.error(traceback.format_exc())

	@property
	def has_dependencies(self):
		for filename, _ in DEPENDENCY_CHOICES:
			try:
				list(self.items(filename))
				return True
			except KeyError:
				pass

	@property
	def dependencies(self):
		for filename, clazz in DEPENDENCY_CHOICES:
			try:
				dependency_files = list(self.items(filename))

				if dependency_files:
					try:
						return clazz().parse(dependency_files[0].content())
					except RequirementParseError:
						logging.exception("Error parsing %s" % dependency_files)
			except KeyError:
				pass

	@property
	def readme_item(self):
		for filename, _ in README_CHOICES:
			try:
				list(self.items(filename))
				return filename
			except KeyError:
				continue

	def archive(self, stream, *args, **kwargs):
		return self.repo.archive(stream, *args, **kwargs)

	def get_config_value(self, section, option, default=None):
		return self.repo_config.get_value(section, option, default)

	def set_list_filter(self, ref, path):
		logging.info("Applying filter: ref=%s, path=%s" % (ref, path))
		self.list_filter_ref = ref
		self.list_filter_path = path.strip('/')

	def items(self, filter_path=None):
		try:
			logging.info("Applying filter_ref %s" % self.list_filter_ref)
			tree = self.repo.tree(self.list_filter_ref)
		except (BadObject, BadName) as bo:
			logging.warning("Got %s - is the repository empty?" % bo)
			return

		path = filter_path or self.list_filter_path
		if path:
			subtree = tree[path]
		else:
			subtree = tree

		if isinstance(subtree, Tree):
			for item in sorted(subtree, key=lambda item: item.type, reverse=True):
				yield item
		else:
			yield subtree

	def get_commit(self, commit_id):
		return self.repo.commit(commit_id)

	def get_latest_commit(self, item):
		# TODO: This should be improved - albeit it seems it's fast as we can get:
		# https://github.com/gitpython-developers/GitPython/issues/240
		if item.hexsha in repo_commit_cache:
			return git.Commit.new(self.repo, repo_commit_cache.get(item.hexsha))
		else:
			logging.info("Listing commits for %s in %s" % (item.path, self.list_filter_ref))
			latest_commit = self.repo.iter_commits(rev=self.list_filter_ref, paths=item.path, max_count=1).next()
			repo_commit_cache.set(item.hexsha, latest_commit.hexsha)
			return latest_commit


class CommitListWrapper(object):
	def __init__(self, repo, filter_ref, filter_path):
		self.repo = repo
		self.filter_ref = filter_ref
		self.filter_path = filter_path
		self._iter_slice = None

	def iter_slice(self, start, stop):
		if self._iter_slice is None:
			start = start or 0
			stop = stop or 20
			self._iter_slice = list(
				self.repo.iter_commits(self.filter_ref, paths=self.filter_path, skip=start, max_count=stop-start)
			)
		return self._iter_slice

	def __len__(self):
		if self.filter_path:
			return long(self.repo.git.rev_list('--count', 'HEAD', '--', self.filter_path))
		else:
			try:
				head = self.repo.head.commit.hexsha
			except ValueError:
				return 0
			commit_count = repo_commit_count_cache.get(head)
			if commit_count:
				return commit_count
			else:
				commit_count = long(self.repo.git.rev_list(self.repo.head.commit, '--count'))
				repo_commit_count_cache.set(head, commit_count)
				return commit_count

	def __nonzero__(self):
		return self.__bool__()

	def __bool__(self):
		return self.__len__() > 0
#
	def __getitem__(self, item):
		if isinstance(item, int):
			return self.iter_slice(None, None)[item]

		logging.info("Slice for start %s, stop %s, step %s" % (item.start, item.stop, item.step))
		return self.iter_slice(item.start, item.stop)