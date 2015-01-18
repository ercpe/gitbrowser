from django.conf.urls import patterns, include, url
from gitbrowser.views.aux import styles
from gitbrowser.views.core import ListRepositoriesView, BrowseTreeView, BrowseBlobView, \
	CommitDetailView

urlpatterns = patterns('',

	url(r'^_styles.css$', styles, name='styles'),

	url(r'^(?P<path>.+)/blob/(?P<ref>[\w\d\-\.]+)/(?P<repo_path>.*)$', BrowseBlobView.as_view(), name='browse_blob'),
	url(r'^(?P<path>.+)/tree/(?P<ref>[\w\d\-\.]+)/(?P<repo_path>.*)$', BrowseTreeView.as_view(), name='browse_ref'),
	url(r'^(?P<path>.+)/commit/(?P<commit_id>[\w\d]{40})$', CommitDetailView.as_view(), name='commit'),
	url(r'^(?P<path>.+)/?$', BrowseTreeView.as_view(), name='browse'),

	url(r'^$', ListRepositoriesView.as_view(), name='list'),
)
