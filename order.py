#!/usr/bin/python3

import json
import time
import ovh
import os
import dotenv
from datetime import datetime, timedelta, timezone
import urllib.request
import logging
from fetcher import fetch_catalog
import threading

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

denv = dotenv.load_dotenv("./.env")

user_preferences={}
try:
    with open("preferences.json") as ff:
        user_preferences = json.load(ff)
    logging.debug("Success opening preferences.json")
except Exception as ex:
    print("Error opening user preferences.")

def save_preferences():
    global user_preferences
    with open("preferences.json","w") as ff:
        json.dump(user_preferences, ff, default=str,indent=2)
    logging.debug("Saved settings file.")

client = ovh.Client()


def fetch_dcs():
    global all_dc
    while True:
        req = urllib.request.Request(
            url="https://eu.api.ovh.com/v1/dedicated/server/datacenter/availabilities?excludeDatacenters=false",
            data=None, 
            headers={"user-agent": "curl"}
            )
        try:
            with urllib.request.urlopen(req,timeout=10) as response:
                all_dc = json.loads(response.read().decode("utf-8"))
                logging.debug("Fetched availabilities: "+str(len(all_dc)))
        except Exception:
            logging.debug("Datacenter fetching failed.")
        time.sleep(3)

def is_dc_available(all, desired, fqn):
    logging.debug("Check availability for FQN "+fqn+" in "+desired)
    for i in all:
        if i["fqn"] == fqn:
            logging.debug("FQN found in availabilities.")
            for j in i["datacenters"]:
                if j["datacenter"] == desired:
                    logging.debug("Datacenter found with this FQN.")
                    if j["availability"] == "unavailable":
                        logging.debug("FQN not available in DC.")
                        return False
                    else:
                        logging.debug("FQN available in this DC.")
                        return True
            return False

def next_cart_expiration_date():
    current_time = datetime.now()
    if current_time.month == 12:
        one_month_later = current_time.replace(month=current_time.year + 1)
    else:
        one_month_later = current_time.replace(month=current_time.month + 1)
    out_string = one_month_later.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    logging.debug("New expiration generated "+out_string)
    return out_string

def init_cart(client):
    logging.debug("Creating a new cart.")
    global user_preferences
    result = client.post("/order/cart",
        expire = next_cart_expiration_date(), # Time of expiration of the cart (type: string)
        ovhSubsidiary = user_preferences["subsidiary"], # OVH Subsidiary where you want to order (type: nichandle.OvhSubsidiaryEnum)
        description = None, # Description of your cart (type: string)
    )
    res2 = client.post("/order/cart/"+result["cartId"]+"/assign")
    logging.debug("Cart created and assigned to your OVH account.")
    return result

def validate_cart(client, cartId, item_ids):
    logging.debug("Validating cart "+cartId)
    logging.debug("Local items in cart "+str(len(item_ids)))
    result={}
    try:
        result = client.get("/order/cart/"+cartId)
        logging.debug("Online items in cart "+str(len(result["items"])))
    except ovh.exceptions.BadParametersError as ex:
        logging.debug("Bad cart ID...")
        return False
    except ovh.exceptions.ResourceNotFoundError as ex:
        logging.debug(ex.args[0])
        return False
    if sorted(result["items"]) != sorted(item_ids):
        logging.debug("Local and online carts are not match!")
        return False
    logging.debug("Local and online carts matching.")
    return True

def is_cart_expired(expiration):
    exp_date = datetime.fromisoformat(expiration)
    current_time = datetime.utcnow()
    difference_seconds = exp_date.timestamp()-current_time.timestamp()
    if difference_seconds <= 120:
        return True
    return False

def fill_cart(client, item, dc):
    result = None
    dedicated_datacenter=dc["dedicated_datacenter"]
    region=dc["region"]
    logging.info("Starting fill cart. The fqn is "+item["fqn"]+" and datacenter is "+dedicated_datacenter)
    try:
        result = client.post("/order/cart/"+item["dc_carts"][dedicated_datacenter]["cartId"]+"/eco",
            planCode = item["planCode"], # Identifier of the offer (type: string)
            pricingMode = "default", # Pricing mode selected for the purchase of the product (type: string)
            quantity = item["qty"], # Quantity of product desired (type: integer)
            duration = "P1M", # Duration selected for the purchase of the product (type: string)
        )
        logging.debug("Server planCode placement ok "+item["planCode"])
    except ovh.exceptions.BadParametersError as ex:
        logging.info("Bad parameter when placing server planCode "+item["planCode"])
        return False
    itemId=result["itemId"]
    server_itemId = result["itemId"]
    logging.debug("Server item ID in cart is "+str(server_itemId))
    item["dc_carts"][dedicated_datacenter]["itemIds"]=[]
    item["dc_carts"][dedicated_datacenter]["itemIds"].append(itemId)
    tmplabels=dict(item["labels"])
    tmplabels["dedicated_datacenter"]=dedicated_datacenter
    tmplabels["region"]=region
    logging.debug("Placing items.")
    for i in tmplabels:
        logging.debug(i+" : "+tmplabels[i])
        result = client.post("/order/cart/"+item["dc_carts"][dedicated_datacenter]["cartId"]+"/item/"+str(itemId)+"/configuration",
            label = i, # Label for your configuration item (type: string)
            value = tmplabels[i], # Value or resource URL on API.OVH.COM of your configuration item (type: string)
        )

    logging.debug("Placing addon planCodes to the item "+str(server_itemId))
    for i in item["addon_planCodes"]:
    # Request body type: order.cart.GenericOptionCreation
        result = client.post("/order/cart/"+item["dc_carts"][dedicated_datacenter]["cartId"]+"/eco/options",
            duration = "P1M", # Duration selected for the purchase of the product (type: string)
            itemId = server_itemId, # Cart item to be linked (type: integer)
            planCode = i, # Identifier of the option offer (type: string)
            pricingMode = "default", # Pricing mode selected for the purchase of the product (type: string)
            quantity = item["qty"], # Quantity of product desired (type: integer)
        )
        itemId=result["itemId"]
        logging.debug("Added planCode "+i+" with ID "+str(itemId))
        item["dc_carts"][dedicated_datacenter]["itemIds"].append(itemId)
    logging.info("OK created cart.")
    return True

def place_order(client, item, dc):
    logging.info("Running validation and order process (depend on your settings).")
    dedicated_datacenter=dc["dedicated_datacenter"]
    result={}
    if "skip_validate" not in item or item["skip_validate"] == False:
        logging.info("Validating the order. Check for cartId in your settings file "+item["dc_carts"][dedicated_datacenter]["cartId"]+" for more info")
        try:
            result = client.get("/order/cart/"+item["dc_carts"][dedicated_datacenter]["cartId"]+"/summary")
        except Exception:
            return False
        logging.info("Iterating cart...")
        for i in result["details"]:
            logging.info(i["description"]+" "+i["detailType"])
            logging.info(str(i["unitPrice"]["value"])+" "+i["unitPrice"]["currencyCode"])
        logging.info("Total: "+str(result["prices"]["withoutTax"]["value"])+" "+str(result["prices"]["withoutTax"]["currencyCode"]))
        item["dc_carts"][dedicated_datacenter]["raw_cart"] = result
        if result["prices"]["withoutTax"]["value"] <= item["ceiling_price"]:
            logging.info("Too expensive! Drop order.")
            item["ceiling_price"] = 0.0
            item["qty"] = 0
            return False
    if "place_order" in item and item["place_order"] == True:
        logging.info("placing an order with this cart.")
        order_result={}
        try:
            order_result = client.post("/order/cart/"+item["dc_carts"][dedicated_datacenter]["cartId"]+"/checkout",
                autoPayWithPreferredPaymentMethod = item["autopay"], # Indicates that order will be automatically paid with preferred payment method (type: boolean)
                waiveRetractationPeriod = True, # Indicates that order will be processed with waiving retractation period (type: boolean)
            )
            logging.info("Success! Order placed. Check the raw order in the cart for more info!")
        except ovh.exceptions.BadParametersError as ex:
            item["order_error"] = ex
            logging.info(ex)
            return False
        except Exception as ex:
            item["order_error"] = ex
            logging.info(ex)
            return False
        logging.debug("Setting additional vars.")
        item["qty"]-=item["qty"]
        item["ordered_at"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item["ordered_in"]=dedicated_datacenter
        item["dc_carts"][dedicated_datacenter]["raw_order"] = order_result
    else:
        item["qty"]-=item["qty"]
    return True

def add_addons_to_servers():
    global user_preferences, all_dc
    catalog={}
    while True:
        logging.debug("Iterate over catalog fetcher.")
        for i in user_preferences["user_servers"]:
            server=i
            if "fetch_catalog" not in i or i["fetch_catalog"] == {}:
                continue
            if catalog == {}:
                catalog = fetch_catalog(all_dc)
                logging.debug("Downloading catalog and using the module to extract them.")
            if catalog[i["fqn"]]["catalog"] != {}:
                logging.debug("Found catalog for "+i["fqn"])
                catalog_cat = catalog[i["fqn"]]["catalog"]
                for j in server["fetch_catalog"]:
                    if server["fetch_catalog"][j] != "":
                        server["addon_planCodes"].append(server["fetch_catalog"][j])
                    else:
                        if j in catalog_cat["addons"]:
                            if "planCode" in catalog_cat["addons"][j]:
                                server["addon_planCodes"].append(catalog_cat["addons"][j]["planCode"])
                            else:
                                server["addon_planCodes"].append(catalog_cat["addons"][j]["default"])
                logging.debug("Make server catalog fetch empty. so do not fetch for this in next time.")
                server["fetch_catalog"]={}
        time.sleep(30)

def iterate_on():
    global user_preferences, all_dc
    for i in user_preferences["user_servers"]:
        if i["qty"] < 1 or len(i["addon_planCodes"]) < 3:
            continue
        for j in i["datacenters"]:
            dedicated_datacenter=j["dedicated_datacenter"]
            if dedicated_datacenter not in i["dc_carts"] or "cartId" not in i["dc_carts"][dedicated_datacenter]  or "cartExpire" not in i["dc_carts"][dedicated_datacenter] or is_cart_expired(i["dc_carts"][dedicated_datacenter]["cartExpire"]) or not validate_cart(client, i["dc_carts"][dedicated_datacenter]["cartId"], i["dc_carts"][dedicated_datacenter]["itemIds"]):
                cart = init_cart(client)
                i["dc_carts"][dedicated_datacenter]={}
                i["dc_carts"][dedicated_datacenter]["cartId"] = cart["cartId"]
                i["dc_carts"][dedicated_datacenter]["cartExpire"] = cart["expire"]
                fill_cart(client, i, j)
                if i["qty"] >= 1 and len(i["addon_planCodes"]) >= 3 and is_dc_available(all_dc, dedicated_datacenter, i["fqn"]):
                    place_order(client, i, j)
            else:
                if i["qty"] >= 1 and len(i["addon_planCodes"]) >= 3 and is_dc_available(all_dc, dedicated_datacenter, i["fqn"]):
                    place_order(client, i, j)

logging.info("Start thread: availability fetcher")
dc_pull_thread = threading.Thread(target=fetch_dcs)
dc_pull_thread.daemon = True  # Daemonize thread to exit when main program exits
dc_pull_thread.start()

time.sleep(3)
logging.info("Start thread: catalog fetcher")
catalog_pull_thread = threading.Thread(target=add_addons_to_servers)
catalog_pull_thread.daemon = True  # Daemonize thread to exit when main program exits
catalog_pull_thread.start()

while True:
    logging.info("New round.")
    try:
        iterate_on()
    except Exception as ex:
        print(ex)
        pass
        
    save_preferences()
    time.sleep(3)
