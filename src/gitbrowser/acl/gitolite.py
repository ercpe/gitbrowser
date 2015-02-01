# -*- coding: utf-8 -*-

import logging as orig_logging
import os
import re
from gitbrowser.acl.base import ACL, acl_cache
from gitbrowser.conf import config
from gitbrowser.utils.perlcrap import DataDumperReader

class ACLDebugLogWrapper(object):

	def null(self, *args, **kwargs):
		pass

	def __getattr__(self, item):
		if config.acl_debug:
			return getattr(orig_logging, item)
		else:
			return self.null

logging = ACLDebugLogWrapper()

class GitoliteACLDefinition(object):

	def __init__(self, acl):
		self.acl = acl

	@staticmethod
	def from_bigconf(bigconf, repo):
		repo_acl = {}

		# add stuff from big_conf
		for regex, enabled in bigconf.get('patterns', {}).get('groups', {}).items():
			if not enabled == '1':
				logging.info("Got regex in %patterns, with value = %s. Skipping." % enabled)
				continue

			if not re.match(regex, repo.clean_relative_path):
				logging.info("Repository path %s does not match %s" % (repo.clean_relative_path, regex))
				continue

			for group_name in bigconf.get('groups', {}).get(regex, []):
				logging.info("%s belongs to repo group %s" % (repo, group_name))

				for user_or_group, ug_acl in bigconf.get('repos', {}).get(group_name, {}).items():
					l = repo_acl.get(user_or_group, [])
					l.extend([tuple(y) for y in ug_acl])
					repo_acl[user_or_group] = l

		return GitoliteACLDefinition(repo_acl)

	@staticmethod
	def from_splitconf(repo):
		repo_acl = {}
		split_conf_path = os.path.join(repo.repo_path, 'gl-conf')
		split_conf_mtime = os.path.getmtime(split_conf_path)

		split_conf_cache_key = '%s-%s' % (repo.repo_path, split_conf_mtime)
		repo_conf = acl_cache.get(split_conf_cache_key)

		if repo_conf:
			logging.info("Using cached acl for %s (mtime %s)" % (repo, split_conf_mtime))
		else:
			logging.info("Reading split config from %s" % split_conf_path)
			repo_conf = DataDumperReader().read(split_conf_path)
			acl_cache.set(split_conf_cache_key, repo_conf)

		if 'one_repo' in repo_conf:
			one_repo = repo_conf['one_repo']
			assert len(one_repo) == 1, \
				"Expected a single repository in one_repo of %s; got %s" % (repo, len(repo_conf))
			for user_or_group, ug_acl in one_repo[one_repo.keys()[0]].items():
				l = repo_acl.get(user_or_group, [])
				l.extend([tuple(y) for y in ug_acl])
				repo_acl[user_or_group] = l

		return GitoliteACLDefinition(repo_acl)

	def __add__(self, other):
		return GitoliteACLDefinition(dict(self.acl.items() + other.acl.items()))

	def __contains__(self, item):
		return item in self.acl

class GitoliteACL(ACL):

	def __init__(self):
		self.user_groups = {}
		self._bigconf = None
		self.big_conf_path = os.path.join(config.gitolite_home, ".gitolite/conf/gitolite.conf-compiled.pm")

	@property
	def bigconf(self):
		if not self._bigconf:
			big_conf_mtime = os.path.getmtime(self.big_conf_path)
			bc_cache_key = "gl-bigconf-%s" % big_conf_mtime
			self._bigconf = acl_cache.get(bc_cache_key)
			if not self._bigconf:
				self._bigconf = DataDumperReader().read(self.big_conf_path)
				acl_cache.set(bc_cache_key, self._bigconf)
		return self._bigconf

	def read_gl_config(self, repo):
		repo_acl = {}

		repo_acl = GitoliteACLDefinition.from_bigconf(self.bigconf, repo)

		if repo.clean_relative_path in self.bigconf.get('split_conf', {}) and \
			self.bigconf.get('split_conf', {}).get(repo.clean_relative_path, '0') == '1':

			repo_acl = repo_acl + GitoliteACLDefinition.from_splitconf(repo)

		return repo_acl

	def can_read(self, user, repo):
		logging.info(">>>>>>>  CHECKING permissions for %s <<<<<<<<<" % repo)
		effective_acl = self.read_gl_config(repo)

		if user.username in self.user_groups:
			user_group_names = self.user_groups[user.username]
		else:
			user_group_names = ["@%s" % g.name for g in user.groups.all()] + ['@all']
			self.user_groups[user.username] = user_group_names

		logging.info("Groups of %s: %s" % (user, user_group_names))

		if user.username in effective_acl:
			logging.info("Access GRANTED due to one of: %s" % effective_acl[user.username])
			return True

		if any(g in effective_acl for g in user_group_names):
			logging.info("Access GRANTED due to one of the groups: %s" % ', '.join(user_group_names))
			return True

		if user.is_anonymous() and 'gitweb' in effective_acl:
			logging.info("Access GRANTED due to anonymous access (via gitweb user)")
			return True

		logging.warning("Access DENIED for %s to %s" % (user, repo))
		return False