import unittest
from mock import Mock
import mock
from wds.aws import ec2
from wds.persistence import persistence
import datetime

class StubLandlord():
    def load_properties(self):
        print 'loading properties'

    def get_property(self, name, default=None):
        if 'count' in name:
            return '1'
        if 'check.url' in name:
            return 'True'
        if 'healthcheck.method' in name:
            return 'GET'
        if 'healthcheck.port' in name:
            return '9000'
        if 'healthcheck.path' in name:
            return '/public/version.txt'
        return name

class StubNameLandlord():
    def load_properties(self):
        print 'loading properties'

    def get_property(self, name, default=None):
        if 'count' in name:
            return '1'
        return name


class Ec2Test(unittest.TestCase):

    def tearDown(self):
        persistence.clear()

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    @mock.patch('wds.aws.ec2.dns')
    @mock.patch('wds.aws.ec2.time')
    @mock.patch('wds.aws.ec2.Script')
    def test_we_create_only_one_instance(self, mock_script, mock_time, mock_dns, mock_landlord, mock_ec2):
        my_project = 'MyProject'
        project = {'name': ('%s' % my_project), 'version': 'v34', 'type': 'play2', 'stop-time': '18'}
        mock_connection = Mock()
        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.public_dns_name = 'my.awesome.dns.com'
        instance1.update.side_effect = ['pending', 'running']
        reservation = Mock()
        reservation.instances = [instance1]
        mock_connection.run_instances.return_value = reservation
        mock_ec2.connect_to_region.return_value = mock_connection
        mock_landlord.Tenant = StubLandlord
        mock_script.get.return_value = 'TheScript'

        instances = ec2.create_and_start_instances(project)

        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.run_instances.assert_called_with(image_id='deploy.image.id', key_name='deploy.keyfile',
                                                         instance_type='deploy.instance.type',
                                                         subnet_id='deploy.subnet',
                                                         security_group_ids=['deploy.secgroup'], min_count=1,
                                                         max_count=1,
                                                         user_data="TheScript",
                                                         dry_run=False)
        instance1.update.assert_has_calls([mock.call(), mock.call()], any_order=True)
        instance1.add_tags.assert_called_with({'Name': ('environment-%s-1' % my_project),
                                   'Project': my_project,
                                   'Version': 'v34',
                                   'StopTime': '18',
                                   'Environment': 'environment',
                                   'Capability': 'tag.capability',
                                   'Client': 'tag.client',
                                   'Deployer': 'igor'})
        mock_dns.update_dns.assert_called_with('my.awesome.dns.com', project, subdomain=('%s-1' % my_project))
        mock_time.sleep.assert_has_calls([mock.call(30), mock.call(2)])
        self.assertEquals(len(instances), 1)
        self.assertEquals(instances[0], instance1.id)

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    @mock.patch('wds.aws.ec2.dns')
    @mock.patch('wds.aws.ec2.time')
    @mock.patch('wds.aws.ec2.Script')
    def test_we_return_none_when_an_instance_fails(self, mock_script, mock_time, mock_dns, mock_landlord, mock_ec2):
        project = {'name': 'MyProject', 'version': 'v34', 'type': 'play2'}
        mock_connection = Mock()
        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.public_dns_name = 'my.awesome.dns.com'
        instance1.update.side_effect = ['pending', 'running']

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.public_dns_name = 'my.awesome2.dns.com'
        instance2.update.side_effect = ['pending', 'stopped']

        reservation = Mock()
        reservation.instances = [instance1, instance2]
        mock_connection.run_instances.return_value = reservation
        mock_ec2.connect_to_region.return_value = mock_connection
        mock_landlord.Tenant = StubLandlord
        mock_script.get.return_value = 'TheScript'

        instances = ec2.create_and_start_instances(project)

        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.run_instances.assert_called_with(image_id='deploy.image.id', key_name='deploy.keyfile',
                                                         instance_type='deploy.instance.type',
                                                         subnet_id='deploy.subnet',
                                                         security_group_ids=['deploy.secgroup'], min_count=1,
                                                         max_count=1,
                                                         user_data="TheScript",
                                                         dry_run=False)
        instance1.update.assert_has_calls([mock.call(), mock.call()], any_order=True)
        instance2.update.assert_has_calls([mock.call(), mock.call()], any_order=True)
        mock_dns.update_dns.assert_called_with('my.awesome.dns.com', project, subdomain='MyProject-1')
        mock_time.sleep.assert_has_calls([mock.call(30), mock.call(2)])
        self.assertIsNone(instances)

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    @mock.patch('wds.aws.ec2.httplib')
    def test_we_return_the_running_status_from_the_instances(self, mock_httplib, mock_landlord, mock_ec2):
        properties = {'region': 'myRegion', 'environment': 'STAGE', 'domain': 'this.is.awesome'}
        project = {'name': 'MyProject', 'version': 'v34', 'type': 'play2'}
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection
        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.public_dns_name = 'my.awesome.dns.com'
        instance1.update.return_value = 'running'
        instance1.ip_address = '127.0.0.1'

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.public_dns_name = 'my.awesome2.dns.com'
        instance2.update.return_value = 'running'
        instance2.ip_address = '127.0.0.1'

        mock_connection.get_only_instances.return_value = [instance1, instance2]
        instances = ['i-278219', 'i-82715']
        url_connection = Mock()
        response = Mock(status=200)
        url_connection.getresponse.return_value = response
        mock_httplib.HTTPConnection.return_value = url_connection

        self.assertEquals(False, ec2.is_running(None, None))
        self.assertEquals(False, ec2.is_running(None, {}))

        result = ec2.is_running(instances, project)
        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.get_only_instances.assert_called_with(instances)
        # mock_httplib.HTTPConnection.request.assert_called_with("GET", "/ping")
        mock_httplib.HTTPConnection.assert_called_with("my.awesome2.dns.com", 9000)
        self.assertEquals(True, instance1.update.called)
        self.assertEquals(True, instance2.update.called)
        self.assertEquals(True, result)

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    @mock.patch('wds.aws.ec2.httplib')
    def test_we_return_false_if_at_least_one_is_not_running(self, mock_httplib, mock_landlord, mock_ec2):
        project = {'name': 'MyProject', 'version': 'v34', 'type': 'play2'}
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection
        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.public_dns_name = 'my.awesome.dns.com'
        instance1.update.return_value = 'running'

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.public_dns_name = 'my.awesome2.dns.com'
        instance2.update.return_value = 'stopped'
        mock_connection.get_only_instances.return_value = [instance1, instance2]
        instances = ['i-278219', 'i-82715']
        url_connection = Mock()
        response = Mock(status=200)
        url_connection.getresponse.return_value = response
        mock_httplib.HTTPConnection.return_value = url_connection

        self.assertEquals(False, ec2.is_running(None, None))
        self.assertEquals(False, ec2.is_running(None, {}))

        result = ec2.is_running(instances, project)
        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.get_only_instances.assert_called_with(instances)
        self.assertEquals(True, instance1.update.called)
        self.assertEquals(True, instance2.update.called)
        self.assertEquals(False, result)

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_return_false_if_terminate_fails(self, mock_landlord, mock_ec2):
        properties = {'region': 'myRegion', 'environment': 'STAGE', 'domain': 'this.is.awesome'}
        instances = ['i-278219', 'i-82715']
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        mock_connection.terminate_instances.return_value = ['i-278219']

        result = ec2.terminate(instances)
        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.terminate_instances.assert_called_with(instances)
        self.assertEquals(False, result)

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_return_true_if_terminate_succeed_in_wrong_order(self, mock_landlord, mock_ec2):
        properties = {'region': 'myRegion', 'environment': 'STAGE', 'domain': 'this.is.awesome'}
        instances = ['i-278219', 'i-82715']
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        mock_connection.terminate_instances.return_value = ['i-82715', 'i-278219']

        result = ec2.terminate(instances)
        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.terminate_instances.assert_called_with(instances)
        self.assertEquals(True, result)

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_return_true_if_terminate_succeed(self, mock_landlord, mock_ec2):
        properties = {'region': 'myRegion', 'environment': 'STAGE', 'domain': 'this.is.awesome'}
        instances = ['i-278219', 'i-82715']
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection
        mock_connection.terminate_instances.return_value = ['i-278219', 'i-82715']

        result = ec2.terminate(instances)
        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.terminate_instances.assert_called_with(instances)
        self.assertEquals(True, result)

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_can_get_all_instances(self, mock_landlord, mock_ec2):
        persistence.save('Instance1', 'v43')
        persistence.save('Instance2', 'v43')
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.dns_name = '192.1.11.1.dnsname'
        instance1.ip_address = '192.1.11.1'
        instance1.state = 'running'
        instance1.tags = {'Name': 'STAGE-Instance-1', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '8'}
        instance1.launch_time = datetime.date.today().isoformat()
        instance1.image_id = 'ami-192812'

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.dns_name = '192.5.5.5.dnsname'
        instance2.ip_address = '192.5.5.5'
        instance2.state = 'stopped'
        instance2.tags = {'Name': 'Instance2', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '9'}
        instance2.launch_time = datetime.date.today().isoformat()
        instance2.image_id = 'ami-237829'

        mock_connection.get_only_instances.return_value = [instance1, instance2]

        instances = ec2.get_all_instances()

        mock_ec2.connect_to_region.assert_called_with('eu-west-1', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.get_only_instances.assert_called_with(filters={"tag:Deployer": "igor"})
        self.assertEquals(len(instances), 2)
        self.assertEquals(instances[0]['name'], 'Instance-1')
        self.assertEquals(instances[0]['version'], 'v43')
        self.assertEquals(instances[0]['project'], 'Instance')
        self.assertEquals(instances[0]['date'], datetime.date.today().isoformat())
        self.assertEquals(instances[0]['ip'], '192.1.11.1')
        self.assertEquals(instances[0]['status'], 'running')
        self.assertEquals(instances[0]['ami'], 'ami-192812')

        self.assertEquals(instances[1]['name'], 'Instance2')
        self.assertEquals(instances[1]['version'], 'v43')
        self.assertEquals(instances[1]['project'], 'Instance')
        self.assertEquals(instances[1]['date'], datetime.date.today().isoformat())
        self.assertEquals(instances[1]['ip'], '192.5.5.5')
        self.assertEquals(instances[1]['status'], 'stopped')
        self.assertEquals(instances[1]['ami'], 'ami-237829')

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_can_get_all_instances_with_region(self, mock_landlord, mock_ec2):
        persistence.save('Instance1', 'v43')
        persistence.save('Instance2', 'v43')
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.ip_address = '192.1.11.1'
        instance1.state = 'running'
        instance1.launch_time = datetime.date.today().isoformat()
        instance1.tags = {'Name': 'STAGE-Instance-1', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '8'}

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.state = 'stopped'
        instance2.ip_address = None
        instance2.launch_time = datetime.date.today().isoformat()
        instance2.tags = {'Name': 'STAGE-Instance-2', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '9'}

        mock_connection.get_only_instances.return_value = [instance1, instance2]

        instances = ec2.get_all_instances('myRegion')

        mock_ec2.connect_to_region.assert_called_with('myRegion', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.get_only_instances.assert_called_with(filters={"tag:Deployer": "igor"})
        self.assertEquals(len(instances), 2)
        self.assertEquals(instances[0]['name'], 'Instance-1')
        self.assertEquals(instances[0]['version'], 'v43')
        self.assertEquals(instances[0]['stopTime'], '8')
        self.assertEquals(instances[0]['project'], 'Instance')
        self.assertEquals(instances[0]['date'], datetime.date.today().isoformat())
        self.assertEquals(instances[0]['ip'], '192.1.11.1')
        self.assertEquals(instances[0]['status'], 'running')
        self.assertEquals(instances[1]['name'], 'Instance-2')
        self.assertEquals(instances[1]['version'], 'v43')
        self.assertEquals(instances[1]['stopTime'], '9')
        self.assertEquals(instances[1]['project'], 'Instance')
        self.assertEquals(instances[1]['date'], datetime.date.today().isoformat())
        self.assertEquals(instances[1]['ip'], 'None')
        self.assertEquals(instances[1]['status'], 'stopped')

    def test_we_return_false_when_we_pass_an_empty_array(self):
        properties = {'region': 'myRegion', 'environment': 'STAGE', 'domain': 'this.is.awesome'}
        self.assertEquals(False, ec2.terminate([]))

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_merge_the_filters_when_searching_for_instances(self, mock_landlord, mock_ec2):
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        region = "myRegion"

        ec2.get_instances(region=region, filters={'tag:Filter': 'Awesome'})

        mock_ec2.connect_to_region.assert_called_with('myRegion', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.get_only_instances.assert_called_with(filters={"tag:Deployer": "igor", 'tag:Filter': 'Awesome'})


    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_capture_the_checkurl_exception_and_return_false(self, mock_landlord, mock_ec2):
        properties = {'region': 'myRegion', 'environment': 'STAGE', 'domain': 'this.is.awesome'}
        project = {'name': 'MyProject', 'version': 'v34', 'type': 'play2', 'StopTime' : '8'}
        instances_ids = ['blah']

        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.ip_address = '192.1.11.1'
        instance1.state = 'running'
        instance1.launch_time = datetime.date.today().isoformat()
        instance1.tags = {'Name': 'STAGE-Instance-1', 'Project': 'Instance', 'Version': 'v43'}

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.state = 'stopped'
        instance2.ip_address = None
        instance2.launch_time = datetime.date.today().isoformat()
        instance2.tags = {'Name': 'STAGE-Instance-2', 'Project': 'Instance', 'Version': 'v43'}

        mock_connection.get_only_instances.return_value = [instance1, instance2]

        real_function = ec2.check_url

        ec2.check_url = Mock(side_effect=[Exception('BOOM!','I have created an instance and you are wasting money... muahahaha')])

        result = ec2.is_running(instances_ids, project)

        self.assertEquals(False, result)

        ec2.check_url = real_function

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_we_capture_the_checkurl_exception_and_return_false(self, mock_landlord, mock_ec2):
        properties = {'region': 'myRegion', 'environment': 'STAGE', 'domain': 'this.is.awesome'}
        project = {'name': 'MyProject', 'version': 'v34', 'type': 'play2'}
        instances_ids = ['blah']

        mock_landlord.Tenant = StubNameLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.ip_address = '192.1.11.1'
        instance1.state = 'running'
        instance1.launch_time = datetime.date.today().isoformat()
        instance1.tags = {'Name': 'STAGE-Instance-1', 'Project': 'Instance', 'Version': 'v43'}

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.state = 'stopped'
        instance2.ip_address = None
        instance2.launch_time = datetime.date.today().isoformat()
        instance2.tags = {'Name': 'STAGE-Instance-2', 'Project': 'Instance', 'Version': 'v43'}

        mock_connection.get_only_instances.return_value = [instance1, instance2]

        real_function = ec2.check_url

        ec2.check_url = Mock(side_effect=[Exception('BOOM!','I have created an instance and you are wasting money... muahahaha')])

        result = ec2.is_running(instances_ids, project)

        self.assertEquals(False, result)

        ec2.check_url = real_function
        
    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')        
    def test_when_we_get_auto_stop_candidates_the_correct_instances_are_returned(self, mock_landlord, mock_ec2):
        now = datetime.datetime.now()
        fiveHoursAgo = datetime.datetime.now() - datetime.timedelta(hours=5)

        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection
        

        instance0 = Mock()
        instance0.id = 'i-938372'
        instance0.dns_name = '192.1.11.1.dnsname'
        instance0.ip_address = '192.1.11.1'
        instance0.state = 'running'
        instance0.tags = {'Name': 'Instance0ShouldntStop', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '8'}
        instance0.launch_time = fiveHoursAgo.isoformat()
        instance0.image_id = 'ami-192812'
        instance0.stopTime = 'NA'

        instance1 = Mock()
        instance1.id = 'i-938372'
        instance1.dns_name = '192.1.11.1.dnsname'
        instance1.ip_address = '192.1.11.1'
        instance1.state = 'running'
        instance1.tags = {'Name': 'Instance1ShouldStop', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '8'}
        instance1.launch_time = fiveHoursAgo.isoformat()
        instance1.image_id = 'ami-192812'
        instance1.stopTime = now.hour-1

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.dns_name = '192.5.5.5.dnsname'
        instance2.ip_address = '192.5.5.5'
        instance2.state = 'running'
        instance2.tags = {'Name': 'Instance2ShouldStop', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '9'}
        instance2.launch_time = fiveHoursAgo.isoformat()
        instance2.image_id = 'ami-237829'
        instance2.stopTime = now.hour

        instance3 = Mock()
        instance3.id = 'i-542211'
        instance3.dns_name = '192.5.5.5.dnsname'
        instance3.ip_address = '192.5.5.5'
        instance3.state = 'running'
        instance3.tags = {'Name': 'Instance3ShouldntStop', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '9'}
        instance3.launch_time = fiveHoursAgo.isoformat()
        instance3.image_id = 'ami-237829'
        instance3.stopTime = now.hour+1

        instance4 = Mock()
        instance4.id = 'i-542211'
        instance4.dns_name = '192.5.5.5.dnsname'
        instance4.ip_address = '192.5.5.5'
        instance4.state = 'stopped'
        instance4.tags = {'Name': 'Instance4AlreadyStopped', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '9'}
        instance4.launch_time = fiveHoursAgo.isoformat()
        instance4.image_id = 'ami-237829'
        instance4.stopTime = now.hour-1

        instance5 = Mock()
        instance5.id = 'i-542211'
        instance5.dns_name = '192.5.5.5.dnsname'
        instance5.ip_address = '192.5.5.5'
        instance5.state = 'running'
        instance5.tags = {'Name': 'Instance4AlreadyStopped', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '9'}
        instance5.launch_time = now.isoformat()
        instance5.image_id = 'ami-237829'
        instance5.stopTime = now.hour-1

        mock_connection.get_only_instances.return_value = [instance0, instance1, instance2, instance3, instance4, instance5]

        instances = ec2.get_auto_stop_candidates()

        self.assertEquals(len(instances), 2)
        self.assertEquals(instances[0]['name'], 'Instance1ShouldStop')
        self.assertEquals(instances[0]['stopTime'], now.hour-1)
        self.assertLess(instances[0]['launchtime'].hour, now.hour)
        self.assertEquals(instances[1]['name'], 'Instance2ShouldStop')
        self.assertEquals(instances[1]['stopTime'], now.hour)
        self.assertLess(instances[1]['launchtime'].hour, now.hour)