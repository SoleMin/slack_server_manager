import json
from datetime import datetime
from flask import Flask, request, make_response
from slack_sdk import WebClient
import re
from datetime import datetime
import os
channel_id = ""
slack_token=""
args=['server','gpu']
num_rule=re.compile(r'\d+')

app = Flask(__name__)
client = WebClient(slack_token)


def load_data(server_ip):
    with open(f"server_info/{server_ip}.json", "r") as st_json:
        data_json = json.load(st_json)
    return data_json

def get_info(data):
    
    info_txt=f'{"-"*30} server {data["server_ip"]} info {"-"*30} \n'
    gpu_Memo,gpu_CPU,gpu_RAM=data['Memo'],data['CPU'],data['RAM']

    info_txt+=f'Memo: {gpu_Memo}\n'+\
    f'CPU: {gpu_CPU}\n'+\
    f'RAM: {gpu_RAM}\n\n'

    for gpu in data['GPU']:
        gpu_id,gpu_product,gpu_user,gpu_start_date=gpu['id'],gpu['product'],gpu['user'],gpu['start date']
        info_txt+=(f'GPU {gpu_id} ({gpu_product}): user: {gpu_user}, start date : {gpu_start_date}\n')
    info_txt+=f'----------------------------------------------------------------------------- \n'
    return info_txt
    
def enable_gpu(text,call_user,args_dict):

    data=parse_gpu_info(args_dict['server'])
    if args_dict['gpu']== 'all':
        gpus=[i for i in len(data['GPU'])]
    elif int(args_dict['gpu']) >= len(data['GPU']) or int(args_dict['gpu'])<0:
        result={'status':[2],'massage':["invalid gpu number"]}
        return result
    else:
        gpus=[int(args_dict['gpu'])]
    result={'status':[],'massage':[]}

    for gpu_num in gpus:
        if data['GPU'][int(gpu_num)]['user'] != None:
            result['status'].append(0)
            result['massage'].append(f"{args_dict['server']} server {gpu_num}'s GPU already using by {data['GPU'][gpu_num]['user']}")
        else:
            data['GPU'][gpu_num]['user']=call_user
            data['GPU'][gpu_num]['start date']=datetime.today().strftime("%Y-%m-%d")
            with open(f"server_info/{args_dict['server']}.json", "w") as f:
                json.dump(data, f)
            result['status'].append(1)
            result['massage'].append(f"{args_dict['server']} server {args_dict['gpu']}'s GPU begins using by {call_user}")
    return result

def disable_gpu(text,call_user,args_dict):
    
    data=parse_gpu_info(args_dict['server'])
    
    if args_dict['gpu']== 'all':
        gpus=[i for i in len(data['GPU'])]
    elif int(args_dict['gpu']) >= len(data['GPU']) or int(args_dict['gpu'])<0:
        result={'status':[2],'massage':["invalid gpu number"]}
        return result
    else:
        gpus=[int(args_dict['gpu'])]

    result={'status':[],'massage':[]}
    for gpu_num in gpus:

        if data['GPU'][gpu_num]['user'] == None:
            result['status'].append(0)
            result['massage'].append(f"{args_dict['server']} server {args_dict['gpu']}'s GPU No one uses it")

        else:        
            data['GPU'][gpu_num]['user']=None
            data['GPU'][gpu_num]['start date']=None
            
            with open(f"server_info/{args_dict['server']}.json", "w") as f:
                json.dump(data, f)
            result['status'].append(1)
            result['massage'].append(f"{args_dict['server']} server {gpu_num}'s GPU Ended Use")
    return result

def parse_gpu_info(server_ip):
    with open(f"server_info/{server_ip}.json", "r") as f:
        data = json.load(f)
    return data

def parse_args(text):
    args_dict={}
    for arg in args:

        arg_rule=re.compile(f'--{arg} \d+')
        if arg=='gpu' and 'all' in text:
            result='all'
        else:
            result=arg_rule.findall(text)

        if result != []:
            args_dict[arg]=arg_rule.findall(text)[0].replace(f'--{arg} ','')
        else:
            args_dict[arg]=None
    return args_dict

def get_answer(text,call_user,command):

    args_dict=parse_args(text)
    if command != 'help' and args_dict['server']+'.json' not in os.listdir('server_info/'):
        return "invalid server ip"
        
    if 'disable' == command:
        try:
            result=disable_gpu(text,call_user,args_dict)
            status=result['status']
            return '\n'.join(result['massage'])
        except:
            return "error"
    elif 'enable' == command:
        try:
            result=enable_gpu(text,call_user,args_dict)
            status=result['status']
            return '\n'.join(result['massage'])
        except:
            return "error"
    elif 'info' == command:
        
        data=parse_gpu_info(args_dict['server'])
        return get_info(data)

    elif 'help' == command:
        return open('help.txt').read()
    return "UNKOWN COMMEND"
 
 
def event_handler(user_query,command,channel,call_user): 
    try:
        answer = get_answer(user_query,call_user,command)
        result = client.chat_postMessage(channel=channel,text=answer)
        return make_response("ok", 200, )
    except IndexError:
        pass
    message = "[%s] cannot find event handler" % event_type
 
    return make_response(message, 200, {"X-Slack-No-Retry": 1})
 
 
@app.route('/', methods=['POST'])
def hello_there():
    # try:
    #     slack_event = json.loads(request.data)
    #     if "challenge" in slack_event:
    #         return make_response(slack_event["challenge"], 200, {"content_type": "application/json"})
    # except:
    #     pass
    query_word = request.form['text']
    user = request.form['user_name']
    channel_id=request.form['channel_id']
    command=request.form['command'].lstrip('/')
    # try:
    return event_handler(query_word,command,channel_id,user)
    # except:
    #     return make_response("There are no slack request events", 404, {"X-Slack-No-Retry": 1})
 
if __name__ == '__main__':
    app.run(debug=True, port=5002)