from django.conf.urls import patterns, include, url
from gitbrowser.views.aux import styles, ContributerAvatarView
from gitbrowser.views.core import ListRepositoriesView, dev_null
from gitbrowser.views.repository import BrowseTreeView, BrowseBlobView, \
	CommitDetailView, RepositoryCommitsListView, RepositoryTagsView, RepositoryArchiveView, \
	RepositoryTreeData

urlpatterns = patterns('',
	url(r'^favicon\.ico', dev_null),

	url(r'^_gitbrowser_meta/styles.css$', styles, name='styles'),
	url(r'^_gitbrowser_meta/avatar/$', ContributerAvatarView.as_view(), name='avatar'),
	url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
	url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),

	url(r'^(?P<path>.+\.git)/blob/(?P<ref>[\w\d\-\.]+)/(?P<repo_path>.*)$', BrowseBlobView.as_view(), name='browse_blob'),
	url(r'^(?P<path>.+\.git)/_data/(?P<ref>[\w\d\-\.]+)/(?P<repo_path>.*)$', RepositoryTreeData.as_view(), name='tree_data'),
	url(r'^(?P<path>.+\.git)/tree/(?P<ref>[\w\d\-\.]+)/(?P<repo_path>.*)$', BrowseTreeView.as_view(), name='browse_ref'),
	url(r'^(?P<path>.+\.git)/commits/(?P<ref>[\w\d\-\.]+)$', RepositoryCommitsListView.as_view(), name='commits'),
	url(r'^(?P<path>.+\.git)/commit/(?P<commit_id>[\w\d]{40})$', CommitDetailView.as_view(), name='commit'),
	url(r'^(?P<path>.+\.git)/tags/(?P<tag>[\w\d\-\.]+)\.tar\.(?P<format>gz)$', RepositoryArchiveView.as_view(), name='archive'),
	url(r'^(?P<path>.+\.git)/tags/$', RepositoryTagsView.as_view(), name='tags'),
	url(r'^(?P<path>.+\.git)/?$', BrowseTreeView.as_view(), name='browse'),

	url(r'(?P<path>.*)/$', ListRepositoriesView.as_view(), name='list'),
	url(r'^$', ListRepositoriesView.as_view(), name='list'),
)
