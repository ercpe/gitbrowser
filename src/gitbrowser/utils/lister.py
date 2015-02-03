# -*- coding: utf-8 -*-
import logging
import os
import re
import itertools
from gitbrowser.acl.base import ACL
from gitbrowser.conf import config
from gitbrowser.utils.repo import GitRepository

repository_dir_re = re.compile('\.git$')

class GitRepositoryContainer(object):

	def __init__(self, name, relative_path):
		self.name = name
		self.relative_path = relative_path

	def __unicode__(self):
		return self.name


class RepositoryLister(object):

	def __init__(self, acl, *args, **kwargs):
		assert isinstance(acl, ACL)
		self.acl = acl

	def list(self, user, path=''):
		raise NotImplementedError


class GitoliteProjectsFileRepositoryLister(RepositoryLister):

	def __init__(self, acl, *args, **kwargs):
		super(GitoliteProjectsFileRepositoryLister, self).__init__(acl, *args, **kwargs)
		self.repositories_path = os.path.join(config.gitolite_home, 'repositories')
		self.projects_file_path = os.path.join(config.gitolite_home, 'projects.list')

	def list(self, user, path='', flat=True):
		logging.info("Listing repositories for %s in '%s' (flat: %s)" % (user, path, flat))
		readable_repositories = []

		if path and not path.endswith('.git'):
			path = path.rstrip('/') + '/'

		with open(self.projects_file_path, 'r') as f:
			for line in f:
				rel_path = line.strip()

				if not rel_path.startswith(path):
					logging.debug("Repository path %s out of scope for path %s" % (rel_path, path))
					continue

				repo = GitRepository(os.path.join(self.repositories_path, line.strip()), rel_path, user)
				if self.acl.can_read(user, repo):
					readable_repositories.append(repo)

		if flat:
			for x in readable_repositories:
				yield x
			return

		def my_key(obj):
			start = len(path)
			end = obj.relative_path.index('/', start+1) \
					if '/' in obj.relative_path[start:] else \
					len(os.path.basename(obj.relative_path)) * -1
			return obj.relative_path[start:end]

		def repo_or_dir_iter():
			for directory, repos_in_dir in itertools.groupby(readable_repositories, key=my_key):
				if directory == '':
					for r in repos_in_dir:
						yield r
				else:
					yield GitRepositoryContainer(name=directory, relative_path=path + directory.rstrip('/'))

		def repo_dir_cmp(a, b):
			if (isinstance(a, GitRepository) and isinstance(b, GitRepository)) or \
					(isinstance(a, GitRepositoryContainer) and isinstance(b, GitRepositoryContainer)):
				return cmp(a.name, b.name)

			if isinstance(a, GitRepository):
				return 1
			return -1

		for x in sorted(repo_or_dir_iter(), cmp=repo_dir_cmp):
			yield x

	def get_repository(self, user, path):
		logging.info("get_repository for user %s and path '%s'" % (user, path))
		for repo in self.list(user, path=path, flat=True):
			logging.info("Checking: %s" % repo.relative_path)
			if repo.relative_path == path:
				return repo

		logging.error("No repository found in '%s' for user %s" % (path, user))