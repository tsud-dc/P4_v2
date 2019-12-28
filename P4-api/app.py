#!/usr/bin/env python
# coding: utf-8

import os
from flask import Flask, render_template, request
import json
import pymongo
import config
import sys
import setenv

listen_port = os.environ.get('port')
n_def = 50

if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = json.loads(os.environ['VCAP_SERVICES'])
    MONGOCRED = VCAP_SERVICES["mlab"][0]["credentials"]
    client = pymongo.MongoClient(MONGOCRED["uri"])
    DB_NAME = str(MONGOCRED["uri"].split("/")[-1])

# Otherwise, assume running locally with local MongoDB instance    
else:
    print(config.col_name_list)
    client = pymongo.MongoClient('127.0.0.1:27017')
    DB_NAME = config.db_name  ##### Make sure this matches the name of your MongoDB database ######

mng_db = client[DB_NAME]

def db_to_list(db_data):
    ret_list = []
    for data in db_data:
        data_list = list(data.values())
        ret_list.append(data_list)
    ret_list_2 = []
    for data in reversed(ret_list):
        ret_list_2.append(data)
    return ret_list_2

def val_to_float(data_list):
    ret_list = []
    for data in data_list:
        ret_list.append(float(data[1]))
    return ret_list

def calc_vals(data_list):
    d_max = max(data_list)
    d_min = min(data_list)
    
    val = 0
    n_val = len(data_list)
    for i in data_list:
        val += i
    d_ave = round(val/n_val, 2)
    
    return d_max, d_min, d_ave

# Create a Flask instance
app = Flask(__name__)

##### Define routes #####
@app.route('/api/v1/getvals', methods=['GET'])
def proc_data():
    req = request.args
    if len(req) > 0:
        n_records = int(req['records'])
    else:
        n_records = n_def

    ret_list = []
    for col in config.col_name_list:
        env_col = mng_db[col]    
        col_data = env_col.find(projection={'_id':0, 'date':1, 'value':1}).sort('_id', -1).limit(n_records)
        env_col_data = db_to_list(col_data)
        val_col_list = val_to_float(env_col_data)    
        col_max, col_min, col_ave = calc_vals(val_col_list)
        
        for ret_d in [col_max, col_min, col_ave, env_col_data]:
            ret_list.append(ret_d)
    
    data_json = json.dumps(ret_list)
    
    code = 200
    return data_json, code

##### Run the Flask instance, browse to http://<< Host IP or URL >>:80 #####
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', listen_port)), threaded=True)