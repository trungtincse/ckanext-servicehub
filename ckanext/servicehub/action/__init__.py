def get_item_as_list(data_dict,name):
    item=data_dict.get(name,[])
    if isinstance(item,list):
        return item
    else:
        return [item]


