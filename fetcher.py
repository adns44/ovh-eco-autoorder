#!/usr/bin/python3

import urllib.request
import urllib.error
import errno
import time
import json
import datetime
import re

# OVH eco hunter (catalog fetcher)

server_catalog = {}
server_availabilities={}
offers = {}
try:
    with open("offers.json") as ff:
        offers = json.load(ff)
except Exception:
    print("Error opening offers.json. However creating it.")

def save_file():
    global offers
    with open("offers.json","w") as ff:
        json.dump(offers, ff, default=str,indent=2)

def search_addon(planCode):
    global server_availabilities, server_catalog
    data={}
    for addon in server_catalog['addons']:
        if planCode == addon['planCode']:
            data['planCode']=addon["planCode"]
            data['invoiceName']=addon["invoiceName"]
            data['price']=(addon["pricings"][1]["price"]/100000000)
            return data
    return "unknown"

def search_cpu(planCode, invoiceName):
    global server_availabilities, server_catalog
    alter_cpu = "" # invoiceName.split("|")[1].strip()
    for k in server_catalog['products']:
        if k['name'] == planCode:
            cpuinfo = k['blobs']['technical']['server']['cpu']
            cpu_full_name = cpuinfo['brand']+" "+cpuinfo['model']
            return cpu_full_name
    return alter_cpu

def get_labels(configurations):
    labels={}
    for i in configurations:
        labels[i["name"]]=i["values"]
    return labels

def get_addons(addonFamilies, memory_code, storage_code):
    ret_addons={}
    ret_addons["price"]=0.0
    for i in addonFamilies:
        name = i["name"]
        if "mandatory" in i and i["mandatory"] == True:
            if name == "storage":
                in_list=i["addons"]
                if len(in_list) > 1:
                    r = re.compile(storage_code+".*")
                    out_list=list(filter(r.match, in_list))
                elif len(in_list) == 1:
                    out_list = [in_list[0]]
                if len(out_list) > 0:
                    ret_addons["storage"]=search_addon(out_list[0])
                    ret_addons["price"]+=ret_addons["storage"]["price"]
            elif name == "memory":
                in_list=i["addons"]
                if len(in_list) > 1:
                    r = re.compile(memory_code+".*")
                    out_list=list(filter(r.match, in_list))
                elif len(in_list) == 1:
                    out_list = [in_list[0]]
                if len(out_list) > 0:
                    ret_addons["memory"]=search_addon(out_list[0])
                    ret_addons["price"]+=ret_addons["memory"]["price"]
            else:
                ret_addons[name]={}
                ret_addons[name]["mandatory"]=i["mandatory"]
                ret_addons[name]["default"]=i["default"]
                ret_addons[name]["exclusive"]=i["exclusive"]
                ret_addons[name]["defaultAddon"]=search_addon(i["default"])
                tmp = []
                for k in i["addons"]:
                    tmp.append(search_addon(k))
                ret_addons[name]["items"]=tmp
    return ret_addons

def get_range(planCode):
    ranges={
        "sk":"kimsufi",
        "sys":"soyoustart",
        "rise":"rise",
    }
    for i in ranges:
        pattern = re.compile(".*"+i+".*")
        if pattern.match(planCode):
            return ranges[i]
    return "unkown"

def search_server(planCode, memory_code, storage_code):
    global server_availabilities, server_catalog
    server = {}
    for product in server_catalog['plans']:
        if product['planCode'] == planCode:
            server['invoiceName']=product['invoiceName']
            server['addons'] = {}
            server['labels'] = {}
            server["sum_price"]=0.0
            server['slug']=product['invoiceName'].split("|")[0].lower()
            if "range" in product["blobs"]["commercial"]:
                server["range"]=product["blobs"]["commercial"]["range"]
            else:
                server["range"]=get_range(planCode)
            server['price']=(product['pricings'][1]['price']/100000000)
            server["sum_price"]+=server['price']
            server['planCode']=product['planCode']
            server["cpu"]=search_cpu(product['planCode'], server['invoiceName'])
            server["labels"]=get_labels(product["configurations"])
            server["addons"] = get_addons(product["addonFamilies"], memory_code, storage_code)
            server["sum_price"]+=server["addons"]["price"]
    return server

def fetch_offers_and_servers():
    global server_availabilities, server_catalog
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0'}
    try:
        req = urllib.request.Request(
            url="https://www.ovh.ie/engine/apiv6/order/catalog/public/eco?ovhSubsidiary=IE", 
            data=None, 
            headers=headers
        )
        with urllib.request.urlopen(req,timeout=10) as response:
            server_catalog =json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print("error in fetch")
        print(e)
        pass
    return True

def iterate_availabilities(server_availabilities):
    global server_catalog, offers
    for i in server_availabilities:
        planCode=i["planCode"]
        fqn=i["fqn"]
        memory_code=i["memory"]
        storage_code=i["storage"]
        offers[fqn]={}
        offers[fqn]["fqn"]=fqn
        offers[fqn]["planCode"]=planCode
        offers[fqn]["memory"]=memory_code
        offers[fqn]["storage"]=storage_code
        offers[fqn]["catalog"]=search_server(planCode, memory_code, storage_code)

def fetch_catalog(availabilities):
    fetch_offers_and_servers()
    iterate_availabilities(availabilities)
    save_file()
    return offers

