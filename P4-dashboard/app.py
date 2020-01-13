#!/usr/bin/env python
# coding: utf-8

import os
from flask import Flask, render_template, request, send_from_directory
import requests
import matplotlib.pyplot as plt
import json
import glob
import random
import platform
import sys
import glob
import boto3
import api_lb
import config
from config import ecs_test_drive
import setenv

listen_port = os.environ.get('port')

def req_data(req_url):
    ret_vals = requests.get(req_url)
    text_vals = ret_vals.text     
    vals_list = json.loads(text_vals)
    return vals_list

def draw_chart(data_list, f_name):
    time_list = []
    vals_list = []
    for elem in data_list:
        time_list.append(elem[0])
        vals_list.append(float(elem[1]))

    plt.rcParams["font.size"] = 8 
    plt.figure(figsize=(4, 5))
    plt.xticks(color="None")
    plt.tick_params(length=0)
    plt.title('{} to {}'.format(time_list[0], time_list[-1]), fontsize=8)
    plt.plot(time_list, vals_list)

    plt.savefig('./charts/{}.png'.format(f_name))
    plt.show()

    
def upload_chart(dir_name, file_list):
    # Get ECS credentials from external config file
    ecs_endpoint_url = ecs_test_drive['ecs_endpoint_url']
    ecs_access_key_id = ecs_test_drive['ecs_access_key_id']  
    ecs_secret_key = ecs_test_drive['ecs_secret_key']
    ecs_bucket_name = ecs_test_drive['ecs_bucket_name']
 
    # Open a session with ECS using the S3 API
    session = boto3.resource(service_name='s3', aws_access_key_id=ecs_access_key_id, aws_secret_access_key=ecs_secret_key, endpoint_url=ecs_endpoint_url)

    # Remove unsupported characters from filename
    #filename = secure_filename(file.filename)

    ## Upload the original image to ECS
    for file in file_list:
        file = file + ".png"
        session.Object(ecs_bucket_name, file).put(Body=open(dir_name + '/' + file, 'rb'), ACL='public-read')

        # Delete the local files
        os.remove('charts/' + file)
    
# Create a Flask instance
app = Flask(__name__)

##### Define routes #####
@app.route('/', methods=['GET', 'POST'])
def home():
    req = request.args
      
    if len(req) > 0:
        req_uri = '{}?records={}'.format(config.uri, req['records'])
    else:
        req_uri = config.uri

    url_list = api_lb.make_url_list(config.api_hosts, config.port, req_uri)

    err_msg = "Connecting DB API is not running"
    vals_list = api_lb.connect_lb(url_list, err_msg, 'load')
    
    if type(vals_list) is list:    
        light_list = vals_list.pop(3)
        temp_list = vals_list.pop(6)

        rand_fn = ''
        for i in range(5):
            rand_fn += str(random.randint(0, 9))

        bri_fname = 'bri_' + str(rand_fn)
        temp_fname = 'temp_' + str(rand_fn)

        draw_chart(light_list, bri_fname)
        draw_chart(temp_list, temp_fname)
        
        upload_chart('charts', [bri_fname, temp_fname])

        bri_ch_val = "src=http://{}.public.ecstestdrive.com/{}/{}.png".format(ecs_test_drive['ecs_access_key_id'].split('@')[0], ecs_test_drive['ecs_bucket_name'], bri_fname)
        temp_ch_val = "src=http://{}.public.ecstestdrive.com/{}/{}.png".format(ecs_test_drive['ecs_access_key_id'].split('@')[0], ecs_test_drive['ecs_bucket_name'], temp_fname)
        
        return render_template('default.html', b_max_val = vals_list[0], b_min_val = vals_list[1], b_mean_val = vals_list[2], t_max_val = vals_list[3], t_min_val = vals_list[4], t_mean_val = vals_list[5], bri_ch = bri_ch_val, temp_ch = temp_ch_val)
    else:
        return(vals_list)



##### Run the Flask instance, browse to http://<< Host IP or URL >>:80 #####
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', listen_port)))
