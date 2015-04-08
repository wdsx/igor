import mock
from mock import Mock
import unittest
from wds.aws import loadbalancer
from boto.exception import BotoServerError


class StubLandlord():
    def load_properties(self):
        print 'loading properties'
    def get_property(self, name):
        return name


class LoadBalancerTest(unittest.TestCase):

    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    def test_we_get_an_existent_lb(self, mock_landlord, mock_lb):
        project = {'name': 'MyProject', 'version': 'v34'}
        mock_connection = Mock()
        mock_connection.get_all_load_balancers.return_value = [1, 2]
        mock_lb.connect_to_region.return_value = mock_connection
        mock_landlord.Tenant = StubLandlord

        result = loadbalancer.get_loadbalancer(project)

        mock_lb.connect_to_region.assert_called_with("deploy.region", aws_access_key_id="aws.id", aws_secret_access_key="aws.secret")
        mock_connection.get_all_load_balancers.assert_called_with(load_balancer_names=['environment-lb-MyProject'])

        assert result == 1


    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    @mock.patch('wds.aws.loadbalancer.dns')
    def test_we_create_a_load_balancer_when_we_raised_an_exception(self, mock_dns, mock_landlord, mock_lb):
        project = {'name': 'MyProject', 'version': 'v34'}
        mock_connection = Mock()
        mock_connection.get_all_load_balancers.side_effect = BotoServerError('oops', 'Boom!')
        returned_load_balancer = Mock()
        returned_load_balancer.dns_name = 'dns_name'
        mock_connection.create_load_balancer.return_value = returned_load_balancer
        mock_lb.connect_to_region.return_value = mock_connection
        mock_landlord.Tenant = StubLandlord

        result = loadbalancer.get_loadbalancer(project)

        mock_lb.connect_to_region.assert_called_with("deploy.region", aws_access_key_id="aws.id", aws_secret_access_key="aws.secret")
        mock_connection.get_all_load_balancers.assert_called_with(load_balancer_names=['environment-lb-MyProject'])
        mock_dns.update_dns.assert_called_with('dns_name', project)
        health_check = returned_load_balancer.configure_health_check.call_args_list[0][0][0]
        assert health_check.interval == 20
        assert health_check.healthy_threshold == 3
        assert health_check.unhealthy_threshold == 5
        assert health_check.target == 'HTTP:9000/public/version.txt'

        assert result == returned_load_balancer

    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    @mock.patch('wds.aws.loadbalancer.dns')
    def test_we_create_a_load_balancer_when_there_is_no_one_yet(self, mock_dns, mock_landlord, mock_lb):
        project = {'name': 'MyProject', 'version': 'v34'}
        mock_connection = Mock()
        mock_connection.get_all_load_balancers.return_value = None
        returned_load_balancer = Mock()
        returned_load_balancer.dns_name = 'dns_name'
        returned_load_balancer.instances = ['a', 'b']
        mock_connection.create_load_balancer.return_value = returned_load_balancer
        mock_lb.connect_to_region.return_value = mock_connection
        mock_landlord.Tenant = StubLandlord

        result = loadbalancer.get_loadbalancer(project)

        mock_lb.connect_to_region.assert_called_with("deploy.region", aws_access_key_id="aws.id", aws_secret_access_key="aws.secret")
        mock_connection.get_all_load_balancers.assert_called_with(load_balancer_names=['environment-lb-MyProject'])
        mock_dns.update_dns.assert_called_with('dns_name', project)
        health_check = returned_load_balancer.configure_health_check.call_args_list[0][0][0]
        assert health_check.interval == 20
        assert health_check.healthy_threshold == 3
        assert health_check.unhealthy_threshold == 5
        assert health_check.target == 'HTTP:9000/public/version.txt'

        assert result == returned_load_balancer
        self.assertEquals(['a', 'b'], returned_load_balancer.instances)

    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    def test_we_dettach_instances_from_the_load_balancer(self, mock_landlord, mock_lb):
        load_balancer = Mock()
        mock_connection = Mock()
        mock_landlord.Tenant = StubLandlord
        mock_lb.connect_to_region.return_value = mock_connection
        load_balancer.name = "MyLoadBalancer"
        instances = ['a', 'b']

        loadbalancer.dettach(load_balancer, instances)

        mock_lb.connect_to_region.assert_called_with("deploy.region", aws_access_key_id="aws.id", aws_secret_access_key="aws.secret")
        mock_connection.deregister_instances.assert_called_with("MyLoadBalancer", instances)

    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    def test_we_attach_instances_to_the_load_balancer(self, mock_landlord, mock_lb):
        load_balancer = Mock()
        mock_connection = Mock()
        mock_landlord.Tenant = StubLandlord
        mock_lb.connect_to_region.return_value = mock_connection
        load_balancer.name = "MyLoadBalancer"
        instances = ['a', 'b']

        loadbalancer.attach(load_balancer, instances)

        mock_lb.connect_to_region.assert_called_with("deploy.region", aws_access_key_id="aws.id", aws_secret_access_key="aws.secret")
        mock_connection.register_instances.assert_called_with("MyLoadBalancer", instances)

    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    def test_we_dont_call_register_when_the_instaces_are_none(self, mock_landlord, mock_lb):
        load_balancer = Mock()
        mock_connection = Mock()
        mock_landlord.Tenant = StubLandlord
        mock_lb.connect_to_region.return_value = mock_connection
        load_balancer.name = "MyLoadBalancer"
        instances = None

        loadbalancer.attach(load_balancer, instances)

        assert not mock_lb.connect_to_region.called
        assert not mock_connection.register_instances.called


    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    def test_we_dont_call_register_when_the_instaces_are_empty(self, mock_landlord, mock_lb):
        load_balancer = Mock()
        mock_connection = Mock()
        mock_landlord.Tenant = StubLandlord
        mock_lb.connect_to_region.return_value = mock_connection
        load_balancer.name = "MyLoadBalancer"
        instances = []

        loadbalancer.attach(load_balancer, instances)

        assert not mock_lb.connect_to_region.called
        assert not mock_connection.register_instances.called


    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    def test_we_dont_call_deregister_when_the_instaces_are_none(self, mock_landlord, mock_lb):
        load_balancer = Mock()
        mock_connection = Mock()
        mock_landlord.Tenant = StubLandlord
        mock_lb.connect_to_region.return_value = mock_connection
        load_balancer.name = "MyLoadBalancer"
        instances = None

        loadbalancer.dettach(load_balancer, instances)

        assert not mock_lb.connect_to_region.called
        assert not mock_connection.deregister_instances.called

    @mock.patch('wds.aws.loadbalancer.elb')
    @mock.patch('wds.aws.loadbalancer.landlord')
    def test_we_dont_call_deregister_when_the_instaces_are_empty(self, mock_landlord, mock_lb):
        load_balancer = Mock()
        mock_connection = Mock()
        mock_landlord.Tenant = StubLandlord
        mock_lb.connect_to_region.return_value = mock_connection
        load_balancer.name = "MyLoadBalancer"
        instances = []

        loadbalancer.dettach(load_balancer, instances)

        assert not mock_lb.connect_to_region.called
        assert not mock_connection.deregister_instances.called



