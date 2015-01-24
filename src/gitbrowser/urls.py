from django.conf.urls import patterns, include, url
from gitbrowser.views.aux import styles, ContributerAvatarView
from gitbrowser.views.core import ListRepositoriesView, BrowseTreeView, BrowseBlobView, \
	CommitDetailView, RepositoryCommitsListView, RepositoryTagsView, RepositoryArchiveView

urlpatterns = patterns('',

	url(r'^_styles.css$', styles, name='styles'),

	url(r'^(?P<path>.+)/blob/(?P<ref>[\w\d\-\.]+)/(?P<repo_path>.*)$', BrowseBlobView.as_view(), name='browse_blob'),
	url(r'^(?P<path>.+)/tree/(?P<ref>[\w\d\-\.]+)/(?P<repo_path>.*)$', BrowseTreeView.as_view(), name='browse_ref'),
	url(r'^(?P<path>.+)/commits/(?P<ref>[\w\d\-\.]+)$', RepositoryCommitsListView.as_view(), name='commits'),
	url(r'^(?P<path>.+)/commit/(?P<commit_id>[\w\d]{40})$', CommitDetailView.as_view(), name='commit'),
	url(r'^(?P<path>.+)/avatar/$', ContributerAvatarView.as_view(), name='avatar'),
	url(r'^(?P<path>.+)/tags/(?P<tag>[\w\d\-\.]+)\.tar\.(?P<format>gz)$', RepositoryArchiveView.as_view(), name='archive'),
	url(r'^(?P<path>.+)/tags/$', RepositoryTagsView.as_view(), name='tags'),
	url(r'^(?P<path>.+)/?$', BrowseTreeView.as_view(), name='browse'),

	url(r'^$', ListRepositoriesView.as_view(), name='list'),
)
