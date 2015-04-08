from boto.ec2 import elb
from boto.exception import BotoServerError
from boto.ec2.elb import HealthCheck
from wds.landlord import landlord
from wds.aws import dns


def get_loadbalancer(project):
    tenant = landlord.Tenant()
    tenant.load_properties()
    conn = elb.connect_to_region(tenant.get_property('deploy.region'),
                                 aws_access_key_id=tenant.get_property('aws.id'),
                                 aws_secret_access_key=tenant.get_property('aws.secret'))
    try:
        load_balancers = conn.get_all_load_balancers(load_balancer_names=[tenant.get_property('environment')+'-lb-' + project['name']])
        if load_balancers:
            print "[LB] Found load balancer ..."
            return load_balancers[0]
        else:
            raise BotoServerError('LoadBalancerNotFound', 'Load Balancer does not exists')
    except BotoServerError:
        print "[LB] No load balancer, creating one ..."
        #TODO: https://github.com/boto/boto/issues/509
        hc = HealthCheck(
            interval=20,
            healthy_threshold=3,
            unhealthy_threshold=5,
            target='HTTP:9000/public/version.txt')
        ports = [(80, 9000, 'http')]
        lb = conn.create_load_balancer(tenant.get_property('environment')+'-lb-' + project['name'], None, ports, [tenant.get_property('deploy.subnet')])
        dns.update_dns(lb.dns_name, project)
        print "[LB] Configuring health checks ... "
        lb.configure_health_check(hc)
        # TODO: Apply tags
        if lb.instances is None:
            lb.instances = []
        return lb

def attach(load_balancer, instances):
    if instances is not None and len(instances) > 0:
        tenant = landlord.Tenant()
        tenant.load_properties()
        conn = elb.connect_to_region(tenant.get_property('deploy.region'),
                                     aws_access_key_id=tenant.get_property('aws.id'),
                                     aws_secret_access_key=tenant.get_property('aws.secret'))
        conn.register_instances(load_balancer.name, instances)


def dettach(load_balancer, instances):
    if instances is not None and len(instances) > 0:
        tenant = landlord.Tenant()
        tenant.load_properties()
        conn = elb.connect_to_region(tenant.get_property('deploy.region'),
                                     aws_access_key_id=tenant.get_property('aws.id'),
                                     aws_secret_access_key=tenant.get_property('aws.secret'))
        conn.deregister_instances(load_balancer.name, instances)