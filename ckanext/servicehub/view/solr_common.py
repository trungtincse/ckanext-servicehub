from collections import defaultdict

import six

from ckan.common import request
import ckan.lib.helpers as h


def selected_filtered_fields():
    """
    selected filtered fields. example: user selected organizations 'viettel' and 'vinamilk'
    then selected filtered fields = [('organizations', 'viettel'), ('organizations', 'vinamilk')]
    """
    result = []
    for (param, value) in search_filter_fields():
        result.append((param, value))
    return result


def selected_filtered_fields_grouped():
    # like selected fields, by group by field name
    result = defaultdict(list)
    for (param, value) in search_filter_fields():
        result[param].append(value)
    return result


def query():
    q = request.params.get('q')
    if q:
        return 'text:(%s)' % clean_query(q)
    else:
        return '*:*'


# https://docs.datastax.com/en/dse/5.1/dse-dev/datastax_enterprise/search/siQuerySyntax.html#Escapingcharactersinasolr_query
_bad_chars = {'+', '-', '&&', '||', '!', '(', ')', '"', '~', '*', '?', ':', '^',  '{', '}', '\\', '/'}


def clean_query(q):
    for char in _bad_chars:
        q = q.replace(char, '')
    return q


def remove_char(s, char):
    return s.replace(char, '')


def cuong_remove_url_param(key, value=None, replace=None, controller=None,
                     action=None, extras=None, alternative_url=None):
    ''' Remove one or multiple keys from the current parameters.
    The first parameter can be either a string with the name of the key to
    remove or a list of keys to remove.
    A specific key/value pair can be removed by passing a second value
    argument otherwise all pairs matching the key will be removed. If replace
    is given then a new param key=replace will be added.
    Note that the value and replace parameters only apply to the first key
    provided (or the only one provided if key is a string).

    controller action & extras (dict) are used to create the base url
    via :py:func:`~ckan.lib.helpers.url_for`
    controller & action default to the current ones

    This can be overriden providing an alternative_url, which will be used
    instead.

    '''
    if isinstance(key, six.string_types):
        keys = [key]
    else:
        keys = key

    # params_nopage = [(k, v) for k, v in request.params.items() if k != 'page']
    # params = list(params_nopage)
    params = []
    # https://tedboy.github.io/flask/generated/generated/werkzeug.ImmutableMultiDict.html
    for param in request.params.iterkeys():
        if param == 'page':
            continue
        vals = request.params.getlist(param)
        params.extend((param, v) for v in vals)

    if value:
        params.remove((keys[0], value))
    else:
        for key in keys:
            [params.remove((k, v)) for (k, v) in params[:] if k == key]
    if replace is not None:
        params.append((keys[0], replace))

    if alternative_url:
        return h._url_with_params(alternative_url, params)

    return h._create_url_with_params(params=params, controller=controller,
                                   action=action, extras=extras)


def has_more_facets(facet, limit=None, exclude_active=False):
    '''
    Returns True if there are more facet items for the given facet than the
    limit.

    Reads the complete list of facet items for the given facet from
    c.search_facets, and filters out the facet items that the user has already
    selected.

    Arguments:
    facet -- the name of the facet to filter.
    limit -- the max. number of facet items.
    exclude_active -- only return unselected facets.

    '''
    facets = []
    for facet_item in c.search_facets.get(facet)['items']:
        # cprint('facet: %s, ["name"]: %s' % (facet, facet_item['name']), end=', ')
        if not len(facet_item['name'].strip()):
            continue
        if not (facet, facet_item['name']) in request.params.items():
            # cprint('active=false')
            facets.append(dict(active=False, **facet_item))
        elif not exclude_active:
            # cprint('active=true')
            facets.append(dict(active=True, **facet_item))
    if c.search_facets_limits and limit is None:
        limit = c.search_facets_limits.get(facet)
    if limit is not None and len(facets) > limit:
        return True
    return False


def search_filter_fields():
    for (param, value) in request.params.items():
        if param not in ['q', 'page', 'sort'] and value != '' and not param.startswith('_'):
            yield param, value

