# openstack-inventory
openstack-inventory is a scripting tool for Ansible, who enables to create dynamic inventories from OpenStack API. Groups, environments and "logical" projects could be defined through metadatas. It also supports the principle of bastion. 

## Functionalities
This program is enable to :
* Retrieve instance list from an OpenStack project, and filter them with `ansible_group`, `environment`, and `project`.
* Dynamically generate a corresponding Ansible inventory, with the associated IP address.
* Include all metadatas of OpenStack's instance into the _meta Ansible section, so you are able to use custom variables during deployment
* Managing the principle of bastion (with SSH Proxy).

## Prerequisites 

### 1. Have a compatible OpenStack project
In order to make this program working, you must define some metadatas on your instances. We are providing the next informations for users who are creating instances through Terraform, but feel free to improve this documentation with other ways. Please also notice that you can edit metadatas directly from the Horizon interface.


Edit your `instances.tf` files, and add :
* For each instance :
```hcl
metadata = {
    ansible_group = "front" #You can set multiple groups using comma : "front,back,db,..."
    environment = "env"
    project = "project" #This is the project in a logical way, not an OpenStack project. It allows you to deploy multiple logical projects in one Openstack project.
  }
```

* For the bastion (optionnal) : You must define that the instance is the bastion.
```hcl
metadata = {
    ansible_group = "bastion" #Do not change this ansible_group name !
    user = "user_name" #Optional : The username used by the script to log in (default is centos)
  }
```

### 2. Installation
In order to use this program on your computer, you must :
1. Have Python (2.7 or 3.x installed), and the `requests` dependency (`pip3 install requests` (Python 3>=), or `pip install requests` (Python 2.7)).
2. Clone this project

## Use the script

### A - For local/test use

1. Copy the OpenStack RC file, and start it, to define your informations in the environment variables : `. ./init.sh` (or `source ./init.sh`).
2. You also have to define `PROJECT_NAME` and `PROJECT_ENV` with your desired informations.
3. Define the `SSH_KEY` variable with the path of your SSH key. It will be used to generate properly the bastion connexion. (If you are not using bastion, you can skip this step)
4. Start `main.py` file.

### B - For use directly in Ansible
1. Copy the OpenStack RC file, and start it, to define your informations in the environment variables : `. ./init.sh` (or `source ./init.sh`).
2. You also have to define `PROJECT_NAME` and `PROJECT_ENV` with your desired informations.
3. Define the `SSH_KEY` variable with the path of your SSH key. It will be used to generate properly the bastion connexion. (If you are not using bastion, you can skip this step)
4. Edit the `ansible-playbook` to tell Ansible to use the program : `ansible-playbook -i ./CLONED_DIR/main.py [...]`.
5. In your Ansible files (notably in `playbook.yml`), replace all `{{inventory_dir}}` by : `inventories/{{lookup('env', 'PROJECT_ENV')}}`).
6. You can deploy !

## Go Further
* In the same spirit of `ansible_group`, you can set multiple `ansible_project` to an instance, by using comma. You can also ask the tool to deploy on several logical projects, using comma in the environment variables (for example : `export PROJECT_NAME="projectA,projectB"`). **BUT**, we are **strongly discouraging this option**, because of the potential consequences of this usage. If there are an `api` group on both `projectA` and `projectB`, you will deploy on all the instances, without differentiation. It could be useful for some things (eg. monitoring tools), but, please, be very careful.
* You can also do this with the `PROJECT_ENV`.
* For the both upside informations, you can also use the wildcard `*` to avoid filtering at all. This is also very, very dangerous. It could be usefull eg. for monitoring or backup tasks, but be very prudent when using it.
* At the beginning, the tool were only designed to go through a bastion, and local IP. We recently added a way to use floating ips, e.g if your infrastructure does not have bastion, or if you need to connect directly to your instances. To enable it, you can use `--fip` argument, or set the `USE_FLOATING_IP` environment variable. In this case, the content of the variable is not checked: If variable is here, it will use FIP.  

## Acknowledgment
We like to thanks [Florian Forestier](https://github.com/Artheriom), [RezoApio](https://github.com/RezoApio), [Jérôme Revillard](https://github.com/jrevillard) and ODA for their work on this tool.

## Legal notice
This program is distributed under [GNU GPL License](https://www.gnu.org/licenses/gpl-3.0.html). be-ys group and contributors are providing this tool "as-is", without any warranty, as defined in the GNU GPL License.

OpenStack® is a trademark of the OpenStack Foundation. All rights reserved.

Ansible is a trademark of RedHat. All rights reserved.

Other trademarks, names and logos are the property of their respective authors.
