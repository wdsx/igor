from wds.aws import ec2, loadbalancer
from wds.igor.environment_tier import EnvironmentTier
from wds.igor.job import JobStatus


def deploy(job):
    job.set_status(JobStatus.running)
    project_attributes = job.get_project()
    new_instances = ec2.create_and_start_instances(project_attributes)
    if ec2.is_running(new_instances, project_attributes):
        if project_attributes.get('environment_tier') == EnvironmentTier.WORKER.value:
            old_instances = ec2.get_instances(filters={'tag:Project': project_attributes['name']})
            old_instance_ids = list(set([instance.id for instance in old_instances]) - set(new_instances))
        else:
            load_balancer = loadbalancer.get_loadbalancer(project_attributes)
            old_instance_ids = [instance.id for instance in load_balancer.instances]
            loadbalancer.attach(load_balancer, new_instances)
            loadbalancer.dettach(load_balancer, old_instance_ids)
        ec2.terminate(old_instance_ids)
        job.set_status(JobStatus.done)
    else:
        ec2.terminate(new_instances)
        job.set_status(JobStatus.failed)


def get_instances():
    return ec2.get_all_instances()