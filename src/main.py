#!/usr/bin/python

# openstack-inventory : Create automatically Ansible inventory through Openstack APIs.
# Copyright (C) 2019 be-ys group and subsidiaries.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import json
import os
import requests
from argparse import ArgumentParser

# Variables from commandline arguments (optional, only here for development purposes)
parser = ArgumentParser()
parser.add_argument("-e", "--env", help="Define the project environment.", default="")
parser.add_argument("-n", "--name", help="Define the project name.", default="")
args, unknown = parser.parse_known_args()

# Variables from Environment.
# OpenStack
user_name = os.getenv("OS_USERNAME")
user_password = os.getenv("OS_PASSWORD")
user_domain = os.getenv("OS_USER_DOMAIN_NAME")
project_id = os.getenv("OS_PROJECT_ID")
auth_api = os.getenv("OS_AUTH_URL")
region_name = os.getenv("OS_REGION_NAME")
# Custom variables for this script
project_env = os.getenv("PROJECT_ENV"),
project_name = os.getenv("PROJECT_NAME")
plainssh_location = os.getenv("SSH_KEY")

compute_api = ""

project_env = args.env if args.env != "" else os.getenv("PROJECT_ENV")
project_name = args.name if args.name != "" else os.getenv("PROJECT_NAME")

project_name = project_name.split(",")

if len(project_name) > 1:
    print("[WARNING] You defined more than one project name ! You are using this function at your own risk.")
    print("[WARNING] For more information, please visit https://github.com/be-ys/openstack-inventory")

# Login
headers = {'Content-Type': 'application/json'}
payload = {"auth": {"identity": {"methods": ["password"], "password": {"user": {"name": user_name, "password": user_password, "domain": {"name": user_domain}}}}, "scope": {"project": {"id": project_id}}}}

login_request = requests.post(url=auth_api+"/auth/tokens", data=json.dumps(payload), headers=headers)
login_request.raise_for_status()

headers = {'X-Auth-Token': login_request.headers.get("X-Subject-Token")}

# Retrieving Compute API URL.
login_result = json.loads(login_request.content)
for cata in login_result["token"]["catalog"]:
    if cata["type"] == "compute" and cata["name"] == "nova":
        for endp in cata["endpoints"]:
            if endp["region"] == region_name and endp["interface"] == "public":
                compute_api = endp["url"]

if compute_api == "":
    print("[FATAL] Compute API not found in auth endpoints. Aborting.")
    exit(0)


instances_rq = requests.get(url=compute_api+"/servers/detail", headers=headers)
instance_file = json.loads(instances_rq.content)

# Initializing variables
inventory = {}
group_list = []
meta = {}


def find_ip(addr_type, addresses):
    for networks in addresses:
        for network in addresses[networks]:
            if network["OS-EXT-IPS:type"] == addr_type:
                return network["addr"]
    return ""


def parse():
    bastion = ""
    for srv in instance_file["servers"]:
        if srv["metadata"] and "ansible_group" in srv["metadata"]:
            # Iterating each server, creating inventory from data we received and getting Bastion's IP.
            if srv["metadata"]["ansible_group"] == "bastion" and plainssh_location is not None:
                user = srv["metadata"]["user"] if "user" in srv["metadata"] else "centos"
                bastion = "-o ProxyCommand='ssh -o StrictHostKeyChecking=no -i " + plainssh_location + " -W %h:%p -q " + user + "@" + find_ip(
                    "floating", srv["addresses"]) + "' -i " + plainssh_location

    for srv in instance_file["servers"]:
        if srv["metadata"] and "environment" in srv["metadata"]:
            if srv["metadata"]["environment"] == project_env and srv["metadata"]["project"] in project_name:
                # Getting IP for this instance
                ip_to_add = find_ip("fixed", srv["addresses"])
                if ip_to_add != "":
                    meta[ip_to_add] = srv["metadata"]
                    meta[ip_to_add]["hostname"] = srv["name"]
                    for group in srv["metadata"]["ansible_group"].split(","):
                        if inventory.get(group):
                            inventory[group]["hosts"].append(ip_to_add)
                        else:
                            group_list.append(group)
                            inventory[group] = {}
                            inventory[group]["hosts"] = [ip_to_add]

    # Ajout des groupes persistents dans l'inventaire.
    inventory["localhost"] = {"hosts": ["localhost"], "vars": {"ansible_connection": "local"}}
    inventory["servers"] = {"children": group_list, "vars": {"ansible_ssh_common_args": bastion}}
    inventory["all"] = {"children": ["localhost", "servers", "ungrouped"]}
    inventory["_meta"] = {"hostvars": meta}
    return inventory


print(json.dumps(parse()))
