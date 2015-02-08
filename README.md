`gitbrowser` is just another attempt to get rid of gitweb. While there are many Git web interfaces, only a few understand gitolite access control lists (gitbrowser only implements the absolute minimum).

# Features
* (basic) support for Gitolite access control lists
* Listing of gitolite repositories via it's `projects.list` file
* Github-like url structure
* Atom feeds for repositories


# Configuration

All configuration is done through a `GITBROWSER` dict in Django's `settings` module.
The following keys are recognized:

- *allow_anonymous* If set to `False`, unauthenticated requests are redirected to the login page
- *clone_url_templates*:
    - either a single string accepting `%(paths)s` for formatting, or
    - a callable accepting `repo, username` as it's argument. The callable should produce a list of strings
- *GL_HOME* path to the home directory for the `git` user. Defaults to `~`.
- *acl* Name of the ACL class in the acl module to use for evaluating permissions. The only implementation is `GitoliteACL`. If you only have public accessible repositories, use `AllowAllACL` here.
- *lister* Name of the lister class to use. The only available implementation is `GitoliteProjectsFileRepositoryLister`, which uses the `projects.list` file in `GL_HOME`


## Display and styling

The `display` sub-dict takes the following keys:

- *list_style*
    - *tree* Repositories are grouped by their relative file system paths
    - *flat* All repositories on a single page
    - *hierarchical* filesystem-like tree structure
- *commit_list_style*
    - *default* multi-line commit list
    - *condensed* 


# Authentication and authorization

If you use an acl implementation different from `AllowAllACL`, make sure your Django user names and group names match those in gitolite. Since it is possible to evaluate group membership on the fly in gitolite, gitbrowser does not use the group memberships defined in gitolite's big conf or split conf. You have to duplicate the group membership in Django

**ATTENTION: DO NOT USE gitbrowser's GitoliteACL implementation if you have permissions other the R(W)+ on .***

gitbrowser does not check for negative permissions (e.g. denied read access) nor does it check for permissions on refs.


# Notes

* If you have repositories with more than a few hundred commits, you should setup a cache using Django's Cache framework.