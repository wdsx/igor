import unittest
from mock import Mock
import mock
from wds.aws import ec2
from wds.persistence import persistence
import datetime
from boto.ec2 import instance

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
        project = {'name': ('%s' % my_project), 'version': 'v34', 'type': 'play2', 'stop-time': '18', 'start-time': '8'}
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
                                   'StartTime': '8',
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
        instance1.tags = {'Name': 'STAGE-Instance-1', 'Project': 'Instance', 'Version': 'v43', 'AutoStopped': 'True'}
        instance1.launch_time = datetime.date.today().isoformat()
        instance1.image_id = 'ami-192812'

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.dns_name = '192.5.5.5.dnsname'
        instance2.ip_address = '192.5.5.5'
        instance2.state = 'stopped'
        instance2.tags = {'Name': 'Instance2', 'Project': 'Instance', 'Version': 'v43'}
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
        self.assertEquals(instances[0]['autoStopped'], 'True')

        self.assertEquals(instances[1]['name'], 'Instance2')
        self.assertEquals(instances[1]['version'], 'v43')
        self.assertEquals(instances[1]['project'], 'Instance')
        self.assertEquals(instances[1]['date'], datetime.date.today().isoformat())
        self.assertEquals(instances[1]['ip'], '192.5.5.5')
        self.assertEquals(instances[1]['status'], 'stopped')
        self.assertEquals(instances[1]['ami'], 'ami-237829')
        self.assertEquals(instances[1]['autoStopped'], 'NA')

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
        instance1.tags = {'Name': 'STAGE-Instance-1', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '8', 'StartTime': '6'}

        instance2 = Mock()
        instance2.id = 'i-542211'
        instance2.state = 'stopped'
        instance2.ip_address = None
        instance2.launch_time = datetime.date.today().isoformat()
        instance2.tags = {'Name': 'STAGE-Instance-2', 'Project': 'Instance', 'Version': 'v43', 'StopTime' : '9', 'StartTime': '7'}

        mock_connection.get_only_instances.return_value = [instance1, instance2]

        instances = ec2.get_all_instances('myRegion')

        mock_ec2.connect_to_region.assert_called_with('myRegion', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.get_only_instances.assert_called_with(filters={"tag:Deployer": "igor"})
        self.assertEquals(len(instances), 2)
        self.assertEquals(instances[0]['name'], 'Instance-1')
        self.assertEquals(instances[0]['version'], 'v43')
        self.assertEquals(instances[0]['stopTime'], '8')
        self.assertEquals(instances[0]['startTime'], '6')
        self.assertEquals(instances[0]['project'], 'Instance')
        self.assertEquals(instances[0]['date'], datetime.date.today().isoformat())
        self.assertEquals(instances[0]['ip'], '192.1.11.1')
        self.assertEquals(instances[0]['status'], 'running')
        self.assertEquals(instances[1]['name'], 'Instance-2')
        self.assertEquals(instances[1]['version'], 'v43')
        self.assertEquals(instances[1]['startTime'], '7')
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
        project = {'name': 'MyProject', 'version': 'v34', 'type': 'play2', 'StopTime' : '8', 'StartTime': '6'}
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
                
    def getStubStopCandidateInstances(self):
        now = datetime.datetime.now()
        fiveHoursAgo = (datetime.datetime.now() - datetime.timedelta(hours=5))
        oneDayAgo = (datetime.datetime.now() - datetime.timedelta(days=1))
        
        stubInstancesToReturn = []
        stubInstancesToReturn.append({'id':'1','name':'Instance0StopTimeNA', 'stopTime':'NA', 'date':fiveHoursAgo.isoformat(), 'status':'running'})
        stubInstancesToReturn.append({'id':'2','name':'Instance1RunningStopTimePassed', 'stopTime':''+str(now.hour - 1)+'', 'date':fiveHoursAgo.isoformat(), 'status':'running'})
        stubInstancesToReturn.append({'id':'3','name':'Instance2RunningButStopTimeNotPassed', 'stopTime':''+str(now.hour + 1)+'', 'date':fiveHoursAgo.isoformat(), 'status':'running'})
        stubInstancesToReturn.append({'id':'4','name':'Instance3RunningStopTimeJustPassed', 'stopTime':''+str(now.hour)+'', 'date':fiveHoursAgo.isoformat(), 'status':'running'})
        stubInstancesToReturn.append({'id':'5','name':'Instance4AlreadyStopped', 'stopTime':''+str(now.hour - 1)+'', 'date':fiveHoursAgo.isoformat(), 'status':'stopped'})
        stubInstancesToReturn.append({'id':'6','name':'Instance5RunningStopTimePassedButLaunchedSinceSameDay', 'stopTime':''+str(now.hour - 1)+'', 'date':now.isoformat(), 'status':'running'})
        stubInstancesToReturn.append({'id':'7','name':'Instance6RunningStopTimePassedButLaunchTIMESinceButPreviousDay', 'stopTime':''+str(now.hour - 1)+'', 'date':oneDayAgo.isoformat(), 'status':'running'})
        stubInstancesToReturn.append({'id':'8','name':'Instance7NoStopTime', 'date':now.isoformat(), 'status':'stopped'})
        return stubInstancesToReturn

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_when_we_get_auto_stop_candidates_the_correct_instances_are_returned(self, mock_landlord, mock_ec2):
        now = datetime.datetime.now()
        fiveHoursAgo = (datetime.datetime.now() - datetime.timedelta(hours=5))
        oneDayAgo = (datetime.datetime.now() - datetime.timedelta(days=1))

        ec2.get_all_instances = Mock(return_value=self.getStubStopCandidateInstances())
        unitInstances = ec2.get_auto_stop_candidates()

        self.assertEquals(len(unitInstances), 3)
        self.assertEquals(unitInstances[0]['id'], '2')
        self.assertEquals(unitInstances[0]['name'], 'Instance1RunningStopTimePassed')
        self.assertEquals(unitInstances[0]['stopTime'], now.hour-1)
        self.assertLess(unitInstances[0]['launchtime'], now.hour)
        
        self.assertEquals(unitInstances[1]['id'], '4')
        self.assertEquals(unitInstances[1]['name'], 'Instance3RunningStopTimeJustPassed')
        self.assertEquals(unitInstances[1]['stopTime'], now.hour)
        self.assertLess(unitInstances[1]['launchtime'], now.hour)
        
        self.assertEquals(unitInstances[2]['id'], '7')
        self.assertEquals(unitInstances[2]['name'], 'Instance6RunningStopTimePassedButLaunchTIMESinceButPreviousDay')
        self.assertEquals(unitInstances[2]['stopTime'], now.hour - 1)
        self.assertGreater(unitInstances[2]['launchtime'], unitInstances[2]['stopTime'])
        
    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_stop_reqeusted_for_ids(self, mock_landlord, mock_ec2):
        instances = ['i-278219', 'i-82715']
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        mockInstance1 = Mock()
        mockInstance2 = Mock()
        mock_connection.stop_instances.return_value = [mockInstance1, mockInstance2]

        ec2.stop(instances)
        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.stop_instances.assert_called_with(instances)
        
    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_stop_not_called_when_reqeusted_ids_is_empty(self, mock_landlord, mock_ec2):
        instances = []
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        ec2.stop(instances)
        
        self.assertEquals(mock_ec2.connect_to_region.call_count, 0);
        self.assertEquals(mock_connection.stop_instances.call_count, 0);
        
    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_tag_added_when_instance_auto_stopped(self, mock_landlord, mock_ec2):
        instances = ['i-278219', 'i-82715']
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        mockInstance1 = Mock()
        mockInstance2 = Mock()
        mock_connection.stop_instances.return_value = [mockInstance1, mockInstance2]
        
        ec2.stop(instances)
        
        mockInstance1.add_tags.assert_called_with({'AutoStopped': 'True'})
        mockInstance2.add_tags.assert_called_with({'AutoStopped': 'True'})
        
    def getStubStartCandidateInstances(self):
        now = datetime.datetime.now()
        fiveHoursAgo = (datetime.datetime.now() - datetime.timedelta(hours=5))
        oneDayAgo = (datetime.datetime.now() - datetime.timedelta(days=1))
        
        stubInstancesToReturn = []
        stubInstancesToReturn.append({'id':'1','name':'Instance0StartTimeNA', 'startTime':'NA', 'date':fiveHoursAgo.isoformat(), 'status':'stopped', 'autoStopped':'True'})
        stubInstancesToReturn.append({'id':'2','name':'Instance1StoppedAndStartTimePassed', 'startTime':''+str(now.hour - 1)+'', 'date':fiveHoursAgo.isoformat(), 'status':'stopped', 'autoStopped':'True'})
        stubInstancesToReturn.append({'id':'3','name':'Instance2StoppedButStopTimeNotPassed', 'startTime':''+str(now.hour + 1)+'', 'date':fiveHoursAgo.isoformat(), 'status':'stopped', 'autoStopped':'True'})
        stubInstancesToReturn.append({'id':'4','name':'Instance3StoppedAndStartTimeTimeJustPassed', 'startTime':''+str(now.hour)+'', 'date':fiveHoursAgo.isoformat(), 'status':'stopped', 'autoStopped':'True'})
        stubInstancesToReturn.append({'id':'5','name':'Instance4AlreadyStarted', 'startTime':''+str(now.hour - 1)+'', 'date':fiveHoursAgo.isoformat(), 'status':'running', 'autoStopped':'True'})
        stubInstancesToReturn.append({'id':'6','name':'Instance5NoStartTime', 'date':now.isoformat(), 'status':'stopped', 'AutoStopped':'True'})
        stubInstancesToReturn.append({'id':'7','name':'Instance6NotStoppedByAutoStopProcess', 'startTime':''+str(now.hour - 1)+'', 'date':fiveHoursAgo.isoformat(), 'status':'stopped'})
        return stubInstancesToReturn

    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_when_we_get_auto_start_candidates_the_correct_instances_are_returned(self, mock_landlord, mock_ec2):
        now = datetime.datetime.now()
        fiveHoursAgo = (datetime.datetime.now() - datetime.timedelta(hours=5))

        ec2.get_all_instances = Mock(return_value=self.getStubStartCandidateInstances())
        unitInstances = ec2.get_auto_start_candidates()

        self.assertEquals(len(unitInstances), 2)
        self.assertEquals(unitInstances[0]['id'], '2')
        self.assertEquals(unitInstances[0]['name'], 'Instance1StoppedAndStartTimePassed')
        
        self.assertEquals(unitInstances[1]['id'], '4')
        self.assertEquals(unitInstances[1]['name'], 'Instance3StoppedAndStartTimeTimeJustPassed')
        
    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_start_reqeusted_for_ids(self, mock_landlord, mock_ec2):
        instances = ['i-278219', 'i-82715']
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        mockInstance1 = Mock()
        mockInstance2 = Mock()
        mock_connection.start_instances.return_value = [mockInstance1, mockInstance2]

        ec2.start(instances)
        mock_ec2.connect_to_region.assert_called_with('deploy.region', aws_access_key_id='aws.id',
                                                      aws_secret_access_key='aws.secret')
        mock_connection.start_instances.assert_called_with(instances)

        
    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_start_not_called_when_reqeusted_ids_is_empty(self, mock_landlord, mock_ec2):
        instances = []
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        ec2.start(instances)
        
        self.assertEquals(mock_ec2.connect_to_region.call_count, 0);
        self.assertEquals(mock_connection.start_instances.call_count, 0);
        
    @mock.patch('wds.aws.ec2.ec2')
    @mock.patch('wds.aws.ec2.landlord')
    def test_autostopped_tag_removed_when_instance_started(self, mock_landlord, mock_ec2):
        instances = ['i-278219', 'i-82715']
        mock_landlord.Tenant = StubLandlord
        mock_connection = Mock()
        mock_ec2.connect_to_region.return_value = mock_connection

        mockInstance1 = Mock()
        mockInstance2 = Mock()
        mock_connection.start_instances.return_value = [mockInstance1, mockInstance2]
        
        ec2.start(instances)
        
        mockInstance1.remove_tags.assert_called_with(['AutoStopped'])
        mockInstance2.remove_tags.assert_called_with(['AutoStopped'])