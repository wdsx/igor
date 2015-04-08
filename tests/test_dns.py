import unittest
from wds.aws import dns
from mock import Mock
import mock

class StubLandlord():
    def load_properties(self):
        print 'loading properties'
    def get_property(self, name):
        if 'environment' in name:
            return "STAGE"
        return "blah.com"

class StubAWSResponse():
    def get(self, name):
        if name == "Id":
            return "/hostedzone/XXXXXXXX"
        return self

class StubResourceRecordSets():
    def __init__(self, connection=None, hosted_zone_id=None):
        self.connection = connection
        self.hosted_zone_id = hosted_zone_id
        self.mock = Mock()
        return self.mock

class DnsTest (unittest.TestCase):

    def test_we_raise_an_exception_if_we_have_no_zone_id(self):
        try:
            dns.get_zone_id(None, "non-existent-domain.com")
        except Exception, e:
            self.assertEquals("The domain non-existent-domain.com is not registered with AWS", e.message)

    def test_we_handle_the_host_zone(self):
        response = Mock()
        response.get.return_value = StubAWSResponse()
        zone_id = dns.get_zone_id(response, "non-existent-domain.com")
        self.assertEquals('XXXXXXXX', zone_id)

    def test_we_get_the_dns_value(self):
        domain = "mydomain.com"
        environment = 'STAGE'
        project = {'name': 'myProject'}
        subdomain = None
        self.assertEquals("myproject.stage.mydomain.com", dns.dns_value(domain, environment, project, subdomain))

        subdomain = "mysubdomain"
        self.assertEquals("mysubdomain.stage.mydomain.com", dns.dns_value(domain, environment, project, subdomain))
    @mock.patch('wds.aws.dns.route53')
    @mock.patch('wds.aws.dns.landlord')
    def test_we_create_the_dns_registry(self, mock_landlord, mock_route53):
        server = "aws.private_dns.resource.server.com"
        project = {'name': 'myProject'}
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_record = Mock()
        mock_connection.get_hosted_zone_by_name.return_value = StubAWSResponse()
        mock_route53.connection.Route53Connection.return_value = mock_connection
        mock_route53.record.Record = mock_record
        mock_route53.record.ResourceRecordSets = Mock()

        dns.update_dns(server, project)

        mock_route53.record.ResourceRecordSets.assert_called_with(connection=mock_connection, hosted_zone_id="XXXXXXXX")
        mock_record.assert_called_with(name="myproject.stage.blah.com", type="CNAME",
                                       resource_records=["aws.private_dns.resource.server.com"], ttl=300)





