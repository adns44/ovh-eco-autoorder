# OVH ECO auto order

## Purpose of this program

OVHcloud changed the ECO line in 2024 September. The new line offers a very insane price-performance ratio so it is easy to know that stocks limited and runs out very fast.

In this program you can place orders VIA the OVHcloud API and start it as a script or in a container and place the order when it is available!

> You are not the only one who use this so your success is not guaranteed

> The API can be changed, removed or software can make any mistake that affects your order so use it on your own risk!

## Set it up

Tested on subsidiary IE, probably work on others but it does not tested.
Project based on [OVHcloud Python wrapper](https://github.com/ovh/python-ovh), consult with this about subsidiary settings and more.

### Set up the API

Create an API key [here](https://api.ovh.com/createToken/index.cgi?GET=/*&PUT=/*&POST=/*&DELETE=/*) and write down its information.
> Note: Select the proper expiration. Best option is 30 days, avoid to use unlimited access, it is more secure if you recreate it every 30 days.
Create a `.env` file to allow dotenv to read it and place the settings in here.
```
OVH_ENDPOINT='ovh-eu'
OVH_APPLICATION_KEY='XXX'
OVH_APPLICATION_SECRET='XXX'
OVH_CONSUMER_KEY='XXX'
```
> Endpoints available on the uper link, use it that matches with your account.
> I suggest to use VsCode to create the files and manage them.

### Set up your desired orders

you need to create the `preferences.json` file.
Here is an example JSON contents for it.

#### RAW JSON
```
{
  "subsidiary": "IE",
  "user_servers": [
    {
      "planCode": "25skleb01",
      "fqn": "25skleb01.ram-32g-ecc-2400.softraid-2x450nvme",
      "skip_validate": false,
      "place_order": false,
      "autopay": false,
      "coupons": ["MONDAY"],
      "datacenters": [
        {
          "region": "europe",
          "dedicated_datacenter": "fra"
        },
        {
          "region": "europe",
          "dedicated_datacenter": "gra"
        }
      ],
      "labels": {
        "dedicated_os": "none_64.en"
      },
      "addon_planCodes": [
        "softraid-2x450nvme-25skle",
        "bandwidth-300-25skle",
        "ram-32g-ecc-2400-25skle"
      ],
      "qty": 1,
      "ceiling_price": 20.0,
      "dc_carts": {}
    }
  ]
}
```

#### Explanation

The JSON contains the order placement subsidiary (IE), and the user servers.

User servers is an array which contains the services. You need to fill an array item by this example but it is important that the script will edit it, store the product-specific cart information and other things. So always write this minimal array item (expand it if you need more than 2 servers) but keep this structure and let the script to use.

A server contains a few important information
- The FQN, planCode, labels, addon planCodes, datacenters.
> These informations  specified on [OVH API](https://eu.api.ovh.com/console/). See order and dedicated server sections.
- QTY and ceiling price are two important variables. Sets the wanted quantity on a cart and sets the maximum monthly price (ex. setup fees). If price higher this the client do not order and set the qty, price to 0 to remove it from future checks.
- From the labels only one needed. Set dedicated_os.
- The dedicated_datacenter is a label too. However if you set it in this JSON structure as in the example, the program simultaneous try to order in FRA and GRA. IF available in FRA or GRA, places and order and set qty to 0 (so stop order). This helps to order a server with multiple DC preferences, if the existence more important than the explicit location for a rare bare metal.
> If you want to place an order both in gra and fra, simply create another item and modify the first to fra-only and second to gra-only. so datacenter array should contains only one element in both servers.
- To the addons you need to place all mandatory addon planCodes. If you do not do it and only one is missing the order fails.
- skip_validate: Set it to true if you want to skip order validation
> If order validation skiped, ceiling price omitted and product ordered on any price. It makes the speed faster.
- place_order: Set it explicitly to true. If you do not do it, only an order plan will be created.
> Keep in mind that if this set to false, the quantity set to 0 after the validation. So if you create an order and only validate it, to order it, close the APP, set quantity and restart it. This behaviour fixes the issue that multiple rechecks increases network load and time consumed by the script.
- autopay: Controls that after the order, payment processed automaticaly or not
> If you set this to false, until you do not pay the order it is not placed so you can lose your chance to get the server.
- coupons: An array which contains the coupon codes for the order
- dc_carts: Empty, it stores the datacenter-specific cart informations. By default do not need manual modification.

So when you first start the script after a personalised configuration, it will fill up the cart information(s) based on your needs.
When it expires (after a month) the script creates a new one.
Only servers checked and planned that have higher qty than zero.

Subsidiary: Depends on your API endpoint. Used at creating orders. You can fetch subsidiary list and select yours, depending on your account.
- [CA](https://ca.api.ovh.com/console/?section=%2Fdedicated%2Fserver&branch=v1#get-/dedicated/server/availabilities)
- [EU](https://eu.api.ovh.com/console/?section=%2Fdedicated%2Fserver&branch=v1#get-/dedicated/server/availabilities)
- [US](https://api.us.ovhcloud.com/console/?section=%2Forder&branch=v1#get-/order/catalog/public/eco)
> always use capitalized letters.

### Autofill from catalog

> This feature is very very experimental. Use it on your own risk!!!

> This feature fetches the EU API catalog. In the future it will be compatible with CA and US.

You can Instruct the API to look the server catalog and fetch the data from it when available.
This feature helps you if you want to grab a server which shown on availability API but not available on the catalog yet. For example KS-LE-2 appeared in October as 25skle02 with low stock in rbx. If you set it you can order it after OVH fills it up into the cart.
If you set up the fetcher, it fetches the data from the catalog and if you set, orders it with your needs.

Here is the raw JSON for this. You can combine multiple servers with multiple options in the array. So for example you can simply insert KS-LE-B and 25skle02.
> Warning: Until one or more than one server requires catalog, it downloaded periodicaly that increases network traffic drasticaly. Use it on your own risk!

```
{
  "subsidiary": "IE",
  "user_servers": [
    {
      "planCode": "24sk50",
      "fqn": "24sk50.ram-32g-ecc-2400.softraid-2x2000sa",
      "skip_validate": false,
      "place_order": false,
      "autopay": false,
      "coupons": ["MONDAY"],
      "fetch_catalog": {
        "storage": "",
        "memory": "",
        "bandwidth": ""
      },
      "datacenters": [
        {
          "region": "europe",
          "dedicated_datacenter": "gra"
        },
        {
          "region": "europe",
          "dedicated_datacenter": "fra"
        }
      ],
      "labels": {
        "dedicated_os": "none_64.en"
      },
      "addon_planCodes": [],
      "qty": 1,
      "ceiling_price": 50.0,
      "dc_carts": {}
    }
  ]
}
```

Explanation:
- The addon_planCodes is empty, it will be filled up when config available on catalog.
- Set in the `fetch_catalog` the parts that you want to fetch. In Kimsufi, these are bandwidth, memory and storage. These are empty strings but if you prefer, you can prefill it up and in this case it only copied to addons. If you ommit any mandatory field, server probably not ordered.
- After filled up the data from catalog, the process is normal. Based on your needs, it creates the raw data and adds it to the json file.
> In rare situations it is possible that FQN and catalog are not consistent, especialy on 500/512 GB NVMe and some special RAM server modells. If only one RAM and storage option possible, it is not a problem as the script uses the default one.

## Run it

run it as a simple Python script
```
pip install -r requirements.txt
python3 order.py
```

Or in Docker (see packages).

If you run it in Docker, bind the `preferences.json` to `/app` directory and bind the `.env` to the `/app` directory. Optionaly bind the `offers.json` if you want to access catalog from the host system.

## Run it in Docker

Clone this repo and run 
`docker compose build`
`docker compose up -d`.

# Remarks

This script uses the OVHcloud API. The ECO and other names are owned by the OVHcloud.
