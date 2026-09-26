#!/usr/bin/env python3
"""Generate Week 07 Terraform JSON; all credentials and state stay outside Git."""
import json
from pathlib import Path
import sys

def build():
    r = {}
    def add(kind, key, **values):
        r.setdefault(kind, {})[key] = values
    def ref(kind, name, attr='id'):
        return '${' + kind + '.' + name + '.' + attr + '}'
    rg=ref('azurerm_resource_group','lab','name')
    loc='swedencentral'
    tags={'Project':'DMI-Week07','Owner':'Eze Favour','ManagedBy':'Terraform','Purpose':'Evidence recovery 2026-09-26'}
    def base(name): return dict(name=name,resource_group_name=rg,location=loc,tags=tags)
    add('azurerm_resource_group','lab',name='dmi-w07-labs-20260926-rg',location=loc,tags=tags)
    add('azurerm_virtual_network','lab',**base('week07-three-tier-vnet'),address_space=['10.0.0.0/16'])
    for tier,prefix in {'web':'10.0.1.0/24','database':'10.0.2.0/24','app':'10.0.4.0/24'}.items():
        values=dict(name=tier+'-subnet',resource_group_name=rg,virtual_network_name=ref('azurerm_virtual_network','lab','name'),address_prefixes=[prefix])
        if tier=='database': values.update(service_endpoints=['Microsoft.Storage'],delegation=[dict(name='mysql',service_delegation=[dict(name='Microsoft.DBforMySQL/flexibleServers',actions=['Microsoft.Network/virtualNetworks/subnets/join/action'])])])
        if tier=='app': values['service_endpoints']=['Microsoft.KeyVault']
        add('azurerm_subnet',tier,**values)
    def rule(name,priority,port,sources,access='Allow',protocol='Tcp'):
        return dict(name=name,priority=priority,direction='Inbound',access=access,protocol=protocol,source_port_range='*',destination_port_range=str(port),source_address_prefixes=sources,destination_address_prefix='*')
    for tier in ['web','app','database']:
        rules=[]
        if tier=='web': rules=[rule('WebHTTP',100,80,['Internet']),rule('OperatorSSH',110,22,['${var.controller_cidr}','10.0.1.10'])]
        if tier=='app': rules=[rule('APIFromWeb',100,5000,['10.0.1.0/24']),rule('SSHFromJump',110,22,['10.0.1.10'])]
        if tier!='database': rules.append(rule('AzureHealthProbe',120,'*',['AzureLoadBalancer']))
        else: rules=[rule('MySQLFromAppAndEpic',100,3306,['10.0.4.0/24','10.0.1.10','10.0.2.0/24'])]
        rules.append(rule('DenyOtherInbound',4000,'*',['*'],'Deny','*'))
        add('azurerm_network_security_group',tier,**base('week07-'+tier+'-nsg'),security_rule=rules)
        add('azurerm_subnet_network_security_group_association',tier,subnet_id=ref('azurerm_subnet',tier),network_security_group_id=ref('azurerm_network_security_group',tier))
    for name in ['web','epic','nat']:
        add('azurerm_public_ip',name,**base('week07-'+name+'-ip'),allocation_method='Static',sku='Standard')
    add('azurerm_nat_gateway','lab',**base('week07-outbound'),sku_name='Standard')
    add('azurerm_nat_gateway_public_ip_association','lab',nat_gateway_id=ref('azurerm_nat_gateway','lab'),public_ip_address_id=ref('azurerm_public_ip','nat'))
    for tier in ['web','app']:
        add('azurerm_subnet_nat_gateway_association',tier,subnet_id=ref('azurerm_subnet',tier),nat_gateway_id=ref('azurerm_nat_gateway','lab'))
    for tier,port in [('web',80),('app',5000)]:
        frontend=dict(name='frontend')
        if tier=='web':frontend['public_ip_address_id']=ref('azurerm_public_ip','web')
        else:frontend.update(subnet_id=ref('azurerm_subnet','app'),private_ip_address='10.0.4.100',private_ip_address_allocation='Static')
        add('azurerm_lb',tier,**base('week07-'+tier+'-lb'),sku='Standard',frontend_ip_configuration=[frontend])
        add('azurerm_lb_backend_address_pool',tier,name=tier+'-pool',loadbalancer_id=ref('azurerm_lb',tier))
        add('azurerm_lb_probe',tier,name=tier+'-health',loadbalancer_id=ref('azurerm_lb',tier),protocol='Http',port=port,request_path='/health',interval_in_seconds=5,number_of_probes=2)
        add('azurerm_lb_rule',tier,name=tier+'-http',loadbalancer_id=ref('azurerm_lb',tier),frontend_ip_configuration_name='frontend',protocol='Tcp',frontend_port=port,backend_port=port,backend_address_pool_ids=[ref('azurerm_lb_backend_address_pool',tier)],probe_id=ref('azurerm_lb_probe',tier),disable_outbound_snat=True)
    machines={'epic':('web','10.0.1.10'),'web1':('web','10.0.1.11'),'web2':('web','10.0.1.12'),'app1':('app','10.0.4.11'),'app2':('app','10.0.4.12')}
    for name,(tier,ip) in machines.items():
        ipc=dict(name='primary',subnet_id=ref('azurerm_subnet',tier),private_ip_address_allocation='Static',private_ip_address=ip)
        if name=='epic':ipc['public_ip_address_id']=ref('azurerm_public_ip','epic')
        add('azurerm_network_interface',name,**base('week07-'+name+'-nic'),ip_configuration=[ipc])
        if name!='epic':add('azurerm_network_interface_backend_address_pool_association',name,network_interface_id=ref('azurerm_network_interface',name),ip_configuration_name='primary',backend_address_pool_id=ref('azurerm_lb_backend_address_pool',tier))
        add('azurerm_linux_virtual_machine',name,**base('week07-'+name),size='Standard_F1als_v7',disk_controller_type='NVMe',zone='2' if name.endswith('2') else '1',admin_username='azureuser',disable_password_authentication=True,network_interface_ids=[ref('azurerm_network_interface',name)],secure_boot_enabled=True,vtpm_enabled=True,boot_diagnostics=[{}],admin_ssh_key=[dict(username='azureuser',public_key='${var.ssh_public_key}')],os_disk=[dict(caching='ReadWrite',storage_account_type='Standard_LRS',disk_size_gb=32)],source_image_reference=[dict(publisher='Canonical',offer='0001-com-ubuntu-server-jammy',sku='22_04-lts-gen2',version='22.04.202608060')],identity=[dict(type='SystemAssigned')],custom_data='${filebase64("bootstrap.sh")}',depends_on=['azurerm_subnet_network_security_group_association.'+tier,'azurerm_subnet_nat_gateway_association.'+tier,'azurerm_nat_gateway_public_ip_association.lab'])
    add('azurerm_private_dns_zone','mysql',name='dmi-w07-20260926.mysql.database.azure.com',resource_group_name=rg,tags=tags)
    add('azurerm_private_dns_zone_virtual_network_link','mysql',name='week07-mysql',resource_group_name=rg,private_dns_zone_name=ref('azurerm_private_dns_zone','mysql','name'),virtual_network_id=ref('azurerm_virtual_network','lab'),registration_enabled=False)
    add('azurerm_mysql_flexible_server','mysql',**base('dmi-w07-20260926-mysql'),administrator_login='week07admin',administrator_password_wo='${var.mysql_password}',administrator_password_wo_version=1,version='8.0.21',sku_name='B_Standard_B1ms',delegated_subnet_id=ref('azurerm_subnet','database'),private_dns_zone_id=ref('azurerm_private_dns_zone','mysql'),public_network_access='Disabled',backup_retention_days=7,geo_redundant_backup_enabled=False,storage=[dict(size_gb=20,auto_grow_enabled=False,io_scaling_enabled=False)],depends_on=['azurerm_private_dns_zone_virtual_network_link.mysql','azurerm_subnet_network_security_group_association.database'])
    for name in ['bookreview','bookstore']:
        add('azurerm_mysql_flexible_database',name,name=name,resource_group_name=rg,server_name=ref('azurerm_mysql_flexible_server','mysql','name'),charset='utf8mb4',collation='utf8mb4_unicode_ci')
    for name,value in [('require_secure_transport','ON'),('tls_version','TLSv1.2')]:
        add('azurerm_mysql_flexible_server_configuration',name,name=name,resource_group_name=rg,server_name=ref('azurerm_mysql_flexible_server','mysql','name'),value=value)
    policies=[dict(tenant_id='${data.azurerm_client_config.current.tenant_id}',object_id='${data.azurerm_client_config.current.object_id}',secret_permissions=['Get','Set','List','Delete','Recover'])]
    for name in ['app1','app2']:
        policies.append(dict(tenant_id='${data.azurerm_client_config.current.tenant_id}',object_id=ref('azurerm_linux_virtual_machine',name,'identity[0].principal_id'),secret_permissions=['Get']))
    for policy in policies:
        policy.update(application_id=None,certificate_permissions=[],key_permissions=[],storage_permissions=[])
    add('azurerm_key_vault','lab',**base('dmiw07kv20260926'),sku_name='standard',tenant_id='${data.azurerm_client_config.current.tenant_id}',soft_delete_retention_days=7,purge_protection_enabled=False,access_policy=policies,network_acls=[dict(default_action='Deny',bypass='AzureServices',ip_rules=['${var.controller_cidr}'],virtual_network_subnet_ids=[ref('azurerm_subnet','app')])])
    for name in ['db-password','jwt-secret']:
        add('azurerm_key_vault_secret',name.replace('-','_'),name=name,key_vault_id=ref('azurerm_key_vault','lab'),value='${var.'+('app_password' if name=='db-password' else 'jwt_secret')+'}',content_type='Week07 application secret',tags=tags)
    add('azurerm_monitor_metric_alert','web',name='week07-web-health-alert',resource_group_name=rg,scopes=[ref('azurerm_lb','web')],description='Detect unhealthy web backend probes.',severity=2,frequency='PT1M',window_size='PT5M',criteria=[dict(metric_namespace='Microsoft.Network/loadBalancers',metric_name='DipAvailability',aggregation='Average',operator='LessThan',threshold=0.99)],tags=tags)
    add('azurerm_resource_group','static',name='mini-finance-rg',location=loc,tags=tags)
    add('azurerm_storage_account','static',name='minifinanceeze20260926',resource_group_name=ref('azurerm_resource_group','static','name'),location=loc,account_tier='Standard',account_replication_type='LRS',min_tls_version='TLS1_2',allow_nested_items_to_be_public=False,tags=tags)
    add('azurerm_storage_account_static_website','static',storage_account_id=ref('azurerm_storage_account','static'),index_document='index.html',error_404_document='index.html')
    # A7's baseline used an unattached NSG with a deliberately broad SSH source.
    # The operator narrowed it to this controller /32 after preserving that report.
    # Keep the recovered safe value as the default for future deployments.
    add('azurerm_network_security_group','audit_fixture',**base('week07-unattached-audit-fixture'),security_rule=[rule('DeliberateAuditSSHFixture',100,22,['${var.controller_cidr}'])])
    variables={name:dict(type='string',sensitive=True) for name in ['mysql_password','app_password','jwt_secret']}
    variables['mysql_password']['ephemeral']=True
    variables.update({name:dict(type='string') for name in ['subscription_id','controller_cidr','ssh_public_key']})
    for key,nsg in r['azurerm_network_security_group'].items():
        for item in nsg.pop('security_rule',[]):
            sources=item.pop('source_address_prefixes')
            if len(sources)==1:item['source_address_prefix']=sources[0]
            else:item['source_address_prefixes']=sources
            add('azurerm_network_security_rule',key+'_'+item['name'],**item,resource_group_name=rg,network_security_group_name=ref('azurerm_network_security_group',key,'name'))
    return dict(terraform=dict(required_version='~> 1.13.5',required_providers=dict(azurerm=dict(source='hashicorp/azurerm',version='=4.47.0'))),provider=dict(azurerm=dict(features=[dict(key_vault=[dict(purge_soft_delete_on_destroy=False)])],subscription_id='${var.subscription_id}',resource_provider_registrations='none')),data=dict(azurerm_client_config=dict(current={})),variable=variables,resource=r,output=dict(web_ip=dict(value=ref('azurerm_public_ip','web','ip_address')),epic_ip=dict(value=ref('azurerm_public_ip','epic','ip_address')),mysql_host=dict(value=ref('azurerm_mysql_flexible_server','mysql','fqdn')),static_endpoint=dict(value=ref('azurerm_storage_account','static','primary_web_endpoint'))))

if __name__=='__main__':
    target=Path(sys.argv[1]);target.mkdir(parents=True,exist_ok=True)
    (target/'main.tf.json').write_text(json.dumps(build(),indent=2)+'\n')
