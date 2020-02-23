import pymongo

client = pymongo.MongoClient(
    "mongodb+srv://ckan_default:ckan_default@cluster0-lsszh.mongodb.net/test?retryWrites=true&w=majority")
db = client["ckan_resource"]
input_col = db["input"]
output_col = db["output"]
req_form_col = db["request_form"]


def insertReqForm(**kwargs):
    label = kwargs['label']
    var_name = kwargs['var_name']
    type = kwargs['type']
    record = dict(
        app_id=kwargs["app_id"],
        fields=[dict(label=x[0], var_name=x[1], type=x[2]) for x in zip(label, var_name, type)]
    )
    req_form_col.insert_one(record)
def findReqForm(app_id):
    return req_form_col.find_one(dict(app_id=app_id))
