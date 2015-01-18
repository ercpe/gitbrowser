# -*- coding: utf-8 -*-
import os
from gitbrowser.utils.acl import ACL
from gitbrowser.utils.repo import GitRepository


class RepositoryLister(object):

	def __init__(self, acl, *args, **kwargs):
		assert isinstance(acl, ACL)
		self.acl = acl

	def get_repositories(self):
		raise NotImplementedError


class GitoliteProjectsFileRepositoryLister(RepositoryLister):

	def __init__(self, acl, *args, **kwargs):
		super(GitoliteProjectsFileRepositoryLister, self).__init__(acl, *args, **kwargs)
		self.gitolite_home = '/var/lib/gitolite'
		self.repositories_path = os.path.join(self.gitolite_home, 'repositories')
		self.projects_file_path = os.path.join(self.gitolite_home, 'projects.list')

	def get_repositories(self, user):
		with open(self.projects_file_path, 'r') as f:
			for line in f:
				rel_path = line.strip()
				repo = GitRepository(os.path.join(self.repositories_path, line.strip()), rel_path)
				if self.acl.can_read(user, repo):
					yield repo

	def get_repository(self, user, path):
		for repo in self.get_repositories(user):
			if repo.relative_path == path:
				return repo