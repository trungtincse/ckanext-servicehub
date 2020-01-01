from  ckan.lib.dictization.model_dictize import *
def service_dictize(group, context,
                  include_groups=True,
                  include_tags=True,
                  include_users=True,
                  include_extras=True,
                  packages_field='datasets',
                  **kw):
    assert packages_field in ('datasets', 'dataset_count', None)
    if packages_field == 'dataset_count':
        dataset_counts = context.get('dataset_counts', None)

    result_dict = d.table_dictize(group, context)
    result_dict.update(kw)

    result_dict['display_name'] = group.app_name

    context['with_capacity'] = True

    context['with_capacity'] = False

    if context.get('for_view'):
        plugin = plugins.IGroupController
        for item in plugins.PluginImplementations(plugin):
            result_dict = item.before_view(result_dict)

    image_url = result_dict.get('image_url')
    result_dict['image_display_url'] = image_url
    if image_url and not image_url.startswith('http'):
        #munge here should not have an effect only doing it incase
        #of potential vulnerability of dodgy api input
        image_url = munge.munge_filename_legacy(image_url)
        result_dict['image_display_url'] = h.url_for_static(
            'uploads/group/%s' % result_dict.get('image_url'),
            qualified=True
        )
    return result_dict
