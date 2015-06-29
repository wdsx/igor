from wds.igor import igor
import unittest
import mock
from wds.igor.job import Job, JobStatus
from wds.igor.environment_tier import EnvironmentTier


class InstanceStub():
    def __init__(self, identifier='i-8w78921'):
        self.id = identifier


class LoadBalancerStub():
    def __init__(self):
        self.instances = [InstanceStub(), InstanceStub()]
        self.dns_name = 'this.is.lb.domain'

class NewLoadBalancerStub():
    def __init__(self):
        self.instances = []
        self.dns_name = 'this.is.lb.domain'


class IgorTest(unittest.TestCase):
    @mock.patch('wds.igor.igor.ec2')
    @mock.patch('wds.igor.igor.loadbalancer')
    def test_we_deploy_in_the_proper_order(self, mock_loadbalancer, mock_ec2):
        project = {'name': 'MyProject', 'version': 'v34', 'environment_tier': EnvironmentTier.WEB_SERVER}
        job = Job(project)
        new_instances = ['i-232425', 'i-3434231']
        mock_ec2.create_and_start_instances.return_value = new_instances
        returned_loadbalancer = LoadBalancerStub()
        mock_loadbalancer.get_loadbalancer.return_value = returned_loadbalancer
        igor.deploy(job)

        mock_ec2.create_and_start_instances.assert_called_with(project)
        mock_loadbalancer.get_loadbalancer.assert_called_with(project)
        mock_ec2.is_running.assert_called_with(new_instances, project)
        mock_loadbalancer.attach.assert_called_with(returned_loadbalancer, new_instances)
        mock_loadbalancer.dettach.assert_called_with(returned_loadbalancer, ['i-8w78921', 'i-8w78921'])
        mock_ec2.terminate.assert_called_with(['i-8w78921', 'i-8w78921'])
        self.assertEquals(JobStatus.done, job.get_status())

    @mock.patch('wds.igor.igor.ec2')
    @mock.patch('wds.igor.igor.loadbalancer')
    def test_we_deploy_an_instance_with_a_load_balancer_by_default(self, mock_loadbalancer, mock_ec2):
        project = {'name': 'MyProject', 'version': 'v34'}
        job = Job(project)
        new_instances = ['i-232425', 'i-3434231']
        mock_ec2.create_and_start_instances.return_value = new_instances
        returned_loadbalancer = LoadBalancerStub()
        mock_loadbalancer.get_loadbalancer.return_value = returned_loadbalancer
        igor.deploy(job)

        mock_ec2.create_and_start_instances.assert_called_with(project)
        mock_loadbalancer.get_loadbalancer.assert_called_with(project)
        mock_ec2.is_running.assert_called_with(new_instances, project)
        mock_loadbalancer.attach.assert_called_with(returned_loadbalancer, new_instances)
        mock_loadbalancer.dettach.assert_called_with(returned_loadbalancer, ['i-8w78921', 'i-8w78921'])
        mock_ec2.terminate.assert_called_with(['i-8w78921', 'i-8w78921'])
        self.assertEquals(JobStatus.done, job.get_status())

    @mock.patch('wds.igor.igor.ec2')
    @mock.patch('wds.igor.igor.loadbalancer')
    def test_we_do_not_call_the_old_instances_if_the_load_balancer_is_new(self, mock_loadbalancer, mock_ec2):
        project = {'name': 'MyProject', 'version': 'v34', 'environment_tier': EnvironmentTier.WEB_SERVER}
        job = Job(project)
        new_instances = ['i-232425', 'i-3434231']
        mock_ec2.create_and_start_instances.return_value = new_instances
        returned_loadbalancer = NewLoadBalancerStub()
        mock_loadbalancer.get_loadbalancer.return_value = returned_loadbalancer

        igor.deploy(job)

        mock_ec2.create_and_start_instances.assert_called_with(project)
        mock_loadbalancer.get_loadbalancer.assert_called_with(project)
        mock_ec2.is_running.assert_called_with(new_instances, project)
        mock_loadbalancer.attach.assert_called_with(returned_loadbalancer, new_instances)
        mock_loadbalancer.dettach.assert_called_with(returned_loadbalancer, [])
        mock_ec2.terminate.assert_called_with([])
        self.assertEquals(JobStatus.done, job.get_status())

    @mock.patch('wds.igor.igor.ec2')
    def test_we_terminate_the_new_instances_if_the_instance_is_not_running(self, mock_ec2):
        project = {'name': 'MyProject', 'version': 'v34'}
        new_instances = ['i-232425', 'i-3434231']
        mock_ec2.is_running.return_value = False
        mock_ec2.create_and_start_instances.return_value = new_instances
        job = Job(project)

        igor.deploy(job)
        mock_ec2.terminate.assert_called_with(new_instances)
        self.assertEquals(JobStatus.failed, job.get_status())

    @mock.patch('wds.igor.igor.ec2')
    @mock.patch('wds.igor.igor.loadbalancer')
    def test_load_balancer_is_not_used_for_worker_projects(self, mock_loadbalancer, mock_ec2):
        project_attributes = {'name': 'MyProject', 'version': 'v34', 'environment_tier': EnvironmentTier.WORKER.value}
        job = Job(project_attributes)
        new_instances = ['i-232425', 'i-3434231']
        old_instance_ids = ['i-232425', 'i-3434231', 'i-342112', 'i-7322912']
        ids_to_terminate = ['i-342112', 'i-7322912']
        old_instances = [InstanceStub(old_instance_ids[2]), InstanceStub(old_instance_ids[3])]
        mock_ec2.is_running.return_value = True
        mock_ec2.create_and_start_instances.return_value = new_instances
        mock_ec2.get_instances.return_value = old_instances

        igor.deploy(job)

        mock_ec2.create_and_start_instances.assert_called_with(project_attributes)
        mock_loadbalancer.get_loadbalancer.assert_not_called_with(project_attributes)
        mock_ec2.terminate.assert_called_with(ids_to_terminate)
        self.assertEquals(JobStatus.done, job.get_status())
        
    @mock.patch('wds.igor.igor.ec2')
    def test_auto_stop_candidates_are_passed_to_ec2_to_stop(self, mock_ec2):
        sampleInstanceIds = [{'id':'i-f6d1190f'},{'id':'i-f6d1190f'}]
        mock_ec2.get_auto_stop_candidates.return_value = sampleInstanceIds
        igor.stop_auto_stop_candidates()
        
        self.assertEquals(mock_ec2.get_auto_stop_candidates.call_count, 1)
        mock_ec2.stop.assert_called_with(['i-f6d1190f','i-f6d1190f'])
        
    @mock.patch('wds.igor.igor.ec2')
    def test_auto_start_candidates_are_passed_to_ec2_to_start(self, mock_ec2):
        sampleInstanceIds = [{'id':'i-f6d1190f'},{'id':'i-f6d1190f'}]
        mock_ec2.get_auto_start_candidates.return_value = sampleInstanceIds
        igor.start_auto_start_candidates()
        
        self.assertEquals(mock_ec2.get_auto_start_candidates.call_count, 1)
        mock_ec2.start.assert_called_with(['i-f6d1190f','i-f6d1190f'])
        
        
