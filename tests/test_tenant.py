import unittest
from wds.landlord import landlord

class ProjectsTest (unittest.TestCase):

    def test_it_should_return_the_properties(self):
        unit = landlord.Tenant()
        unit.load_properties()
        self.assertEqual('AXXXXXXXXXXXXXXXXXX',unit.get_property('aws.id'))
        self.assertEqual('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY', unit.get_property('aws.secret'))
        self.assertEqual('True', unit.get_property('deploy.check.url'))
        self.assertEqual('my-domain.net', unit.get_property('deploy.domain'))
        self.assertEqual('ami-9999999', unit.get_property('deploy.image.id'))
        self.assertEqual('t2.micro', unit.get_property('deploy.instance.type'))
        self.assertEqual('keyfilename', unit.get_property('deploy.keyfile'))
        self.assertEqual('1', unit.get_property('deploy.max_count'))
        self.assertEqual('1', unit.get_property('deploy.min_count'))
        self.assertEqual('eu-west-1', unit.get_property('deploy.region'))
        self.assertEqual('sg-xxxxxxxx', unit.get_property('deploy.secgroup'))
        self.assertEqual('subnet-xxxxxxxx', unit.get_property('deploy.subnet'))
        self.assertEqual('/ping', unit.get_property('healthcheck.endpoint'))
        self.assertEqual('GET', unit.get_property('healthcheck.method'))
        self.assertEqual('/public/version.txt', unit.get_property('healthcheck.path'))
        self.assertEqual('9000', unit.get_property('healthcheck.port'))
        self.assertEqual('Capability', unit.get_property('tag.capability'))
        self.assertEqual('Client', unit.get_property('tag.client'))
        self.assertEqual('xxxxxxxxxxxxxxxxxxxxxxxxxxx', unit.get_property('token'))
        self.assertEqual(None, unit.get_property('commented'))
        self.assertEqual('lol', unit.get_property('commented', 'lol'))



