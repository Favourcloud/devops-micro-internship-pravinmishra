import unittest
from analyze import audit

class AuditTests(unittest.TestCase):
    def baseline(self):
        return dict(nsg=[dict(name='nsg',securityRules=[])],storage=[dict(name='web',allowBlobPublicAccess=False)],disks=[dict(name='disk',encryption=dict(type='EncryptionAtRestWithPlatformKey'),managedBy='vm')],mysql=[dict(name='db',network=dict(publicNetworkAccess='Disabled',delegatedSubnetResourceId='private'))])
    def rule(self,source,port,access='Allow',priority=100):
        return dict(name='rule',direction='Inbound',access=access,protocol='Tcp',priority=priority,sourceAddressPrefix=source,destinationPortRange=port)
    def test_clean(self): self.assertEqual(audit(self.baseline())['overall'],'PASS')
    def test_missing_not_pass(self): self.assertEqual(audit({})['overall'],'WARN')
    def test_port_range(self):
        d=self.baseline();d['nsg'][0]['securityRules']=[self.rule('0.0.0.0/0','20-30')];self.assertEqual(audit(d)['overall'],'FAIL')
    def test_ipv6(self):
        d=self.baseline();d['nsg'][0]['securityRules']=[self.rule('::/0','3389')];self.assertEqual(audit(d)['overall'],'FAIL')
    def test_prior_deny(self):
        d=self.baseline();d['nsg'][0]['securityRules']=[self.rule('*','*','Deny',90),self.rule('Internet','22')];self.assertEqual(audit(d)['overall'],'PASS')
    def test_service_tag_not_internet(self):
        d=self.baseline();d['nsg'][0]['securityRules']=[self.rule('AzureLoadBalancer','*')];self.assertEqual(audit(d)['overall'],'PASS')
    def test_missing_encryption(self):
        d=self.baseline();d['disks'][0]['encryption']={};self.assertEqual(audit(d)['overall'],'WARN')
    def test_failed_query(self):
        d=self.baseline();d['mysql']={'query_error':True};self.assertEqual(audit(d)['overall'],'WARN')
    def test_public_mysql(self):
        d=self.baseline();d['mysql'][0]['network']['publicNetworkAccess']='Enabled';self.assertEqual(audit(d)['overall'],'FAIL')

if __name__=='__main__':unittest.main()
