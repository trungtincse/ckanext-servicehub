import pymongo

client = pymongo.MongoClient(
    "mongodb+srv://ckan_default:ckan_default@cluster0-lsszh.mongodb.net/test?retryWrites=true&w=majority")
db = client["ckan_resource"]
input_col = db["input"]
output_col = db["output"]
req_form_col = db["request_forms"]

def findReqForm(app_id):
    return req_form_col.find_one(dict(app_id=app_id))
