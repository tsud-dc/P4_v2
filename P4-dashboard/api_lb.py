import config
import random
import requests
import json

def make_url_list(hosts_list, port, uri):
    ret_list = []
    for host, lport in zip(hosts_list, port):
        if lport == '80':
            ret_list.append('http://{}{}'.format(host, uri))
        else:
            ret_list.append('http://{}:{}{}'.format(host, lport, uri))
    ret_list = random.sample(ret_list, len(ret_list))
    return ret_list

def req_data(req_url, kind):
    ret_vals = requests.get(req_url)
    if kind == 'load':
        text_vals = ret_vals.text 
        vals_list = json.loads(text_vals)
    else:
        vals_list = ret_vals
    return vals_list
        
def connect_lb(targ_list, err_msg, kind):
    num_targ = len(targ_list)
    for i in range(num_targ):
        try:
            print('try:{}'.format(targ_list[i]))
            vals_list = req_data(targ_list[i], kind)
            return vals_list
        except:
            if i < num_targ:
                continue
    return err_msg
