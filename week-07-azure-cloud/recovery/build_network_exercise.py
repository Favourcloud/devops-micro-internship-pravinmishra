#!/usr/bin/env python3
"""Temporary A3 lab. Delete only its dedicated resource group after proof."""
import json
import base64
from pathlib import Path
import sys

def build():
    r={}
    def add(t,k,**v):r.setdefault(t,{})[k]=v
    def ref(t,k,a='id'):return '${'+t+'.'+k+'.'+a+'}'
    rg=ref('azurerm_resource_group','lab','name')
    def base(name):return dict(name=name,resource_group_name=rg,location='swedencentral',tags={'Project':'DMI-Week07-A3','Purpose':'Temporary evidence exercise'})
    add('azurerm_resource_group','lab',name='vnet-demo-rg',location='swedencentral')
    add('azurerm_virtual_network','lab',**base('eb-demo-vnet'),address_space=['10.0.0.0/16'])
    for name,prefix in [('web','10.0.1.0/24'),('app','10.0.2.0/25'),('db','10.0.3.0/26')]:
        add('azurerm_subnet',name,name=name+'-subnet',resource_group_name=rg,virtual_network_name='eb-demo-vnet',address_prefixes=[prefix],depends_on=['azurerm_virtual_network.lab'])
    add('azurerm_network_security_group','web',**base('web-nginx-nsg'))
    for name,priority,port,source in [('SSH',100,22,'${var.controller_cidr}'),('HTTP',110,80,'Internet')]:
        add('azurerm_network_security_rule',name,name=name,resource_group_name=rg,network_security_group_name=ref('azurerm_network_security_group','web','name'),priority=priority,direction='Inbound',access='Allow',protocol='Tcp',source_port_range='*',destination_port_range=str(port),source_address_prefix=source,destination_address_prefix='*')
    add('azurerm_subnet_network_security_group_association','web',subnet_id=ref('azurerm_subnet','web'),network_security_group_id=ref('azurerm_network_security_group','web'))
    for name in ['web','lb']:add('azurerm_public_ip',name,**base('web-elb-ip' if name=='lb' else 'web-nginx-ip'),allocation_method='Static',sku='Standard')
    add('azurerm_network_interface','web',**base('web-nginx-nic'),ip_configuration=[dict(name='primary',subnet_id=ref('azurerm_subnet','web'),private_ip_address_allocation='Dynamic',public_ip_address_id=ref('azurerm_public_ip','web'))])
    add('azurerm_linux_virtual_machine','web',**base('web-nginx'),size='Standard_F1als_v7',disk_controller_type='NVMe',admin_username='azureuser',disable_password_authentication=True,network_interface_ids=[ref('azurerm_network_interface','web')],admin_ssh_key=[dict(username='azureuser',public_key='${var.ssh_public_key}')],os_disk=[dict(caching='ReadWrite',storage_account_type='Standard_LRS',disk_size_gb=30)],source_image_reference=[dict(publisher='Canonical',offer='0001-com-ubuntu-server-jammy',sku='22_04-lts-gen2',version='22.04.202608060')],custom_data=base64.b64encode(b"#!/bin/bash\nset -eu\napt-get update\napt-get install -y nginx\nsystemctl enable --now nginx\n").decode(),depends_on=['azurerm_subnet_network_security_group_association.web'])
    add('azurerm_lb','web',**base('web-public-elb'),sku='Standard',frontend_ip_configuration=[dict(name='frontend',public_ip_address_id=ref('azurerm_public_ip','lb'))])
    add('azurerm_lb_backend_address_pool','web',name='web-backend-pool',loadbalancer_id=ref('azurerm_lb','web'))
    add('azurerm_network_interface_backend_address_pool_association','web',network_interface_id=ref('azurerm_network_interface','web'),ip_configuration_name='primary',backend_address_pool_id=ref('azurerm_lb_backend_address_pool','web'))
    add('azurerm_lb_probe','web',name='web-health-probe',loadbalancer_id=ref('azurerm_lb','web'),protocol='Tcp',port=80)
    add('azurerm_lb_rule','web',name='web-http-rule',loadbalancer_id=ref('azurerm_lb','web'),frontend_ip_configuration_name='frontend',protocol='Tcp',frontend_port=80,backend_port=80,backend_address_pool_ids=[ref('azurerm_lb_backend_address_pool','web')],probe_id=ref('azurerm_lb_probe','web'))
    return dict(terraform=dict(required_providers=dict(azurerm=dict(source='hashicorp/azurerm',version='=4.47.0'))),provider=dict(azurerm=dict(features=[{}],subscription_id='${var.subscription_id}',resource_provider_registrations='none')),variable={n:dict(type='string') for n in ['subscription_id','controller_cidr','ssh_public_key']},resource=r,output=dict(public_ip=dict(value=ref('azurerm_public_ip','lb','ip_address'))))

if __name__=='__main__':
    p=Path(sys.argv[1]);p.mkdir(parents=True,exist_ok=True);(p/'main.tf.json').write_text(json.dumps(build(),indent=2)+'\n')
