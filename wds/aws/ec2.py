import time
from boto import ec2
from wds.aws import dns
from wds.landlord import landlord
from wds.persistence import persistence
from wds.igor.initscript import Script
import httplib
from retrying import retry


def create_and_start_instances(project):
    tenant = landlord.Tenant()
    tenant.load_properties()
    instance_ids = []
    connection = ec2.connect_to_region(tenant.get_property('deploy.region'),
                                       aws_access_key_id=tenant.get_property('aws.id'),
                                       aws_secret_access_key=tenant.get_property('aws.secret'))
    print "Running instances ..."
    reservations = connection.run_instances(image_id=tenant.get_property('deploy.image.id'),
                                            key_name=tenant.get_property('deploy.keyfile'),
                                            instance_type=tenant.get_property('deploy.instance.type'),
                                            subnet_id=tenant.get_property('deploy.subnet'),
                                            security_group_ids=[tenant.get_property('deploy.secgroup')],
                                            min_count=int(tenant.get_property('deploy.min_count')),
                                            max_count=int(tenant.get_property('deploy.max_count')),
                                            user_data=Script.get(project, tenant.get_property('environment')),
                                            dry_run=False)
    time.sleep(30)
    for index, instance in enumerate(reservations.instances):
        subdomain_name = project['name'] + "-" + str(index+1)
        instance_name = tenant.get_property('environment') + "-" + subdomain_name
        print "Instance %s [%s] checking ..." % (instance.id, instance_name)
        status = instance.update()
        while status == 'pending':
            print "Instance %s is still pending ..." % instance.id
            time.sleep(2)
            status = instance.update()
        if status == 'running':
            instance_ids.append(instance.id)
            print 'New instance %s accessible at %s' % (instance.id, instance.public_dns_name)
            instance.add_tags({'Name': instance_name,
                               'Project': project['name'],
                               'Version': project['version'],
                               'Environment': tenant.get_property('environment'),
                               'Capability': tenant.get_property('tag.capability'),
                               'Client': tenant.get_property('tag.client'),
                               'Deployer': 'igor'})
            print 'Added new Tags, Description and Name to %s' % instance.id
            dns.update_dns(instance.public_dns_name, project, subdomain=subdomain_name)
            #TODO: Delete the instance if catch the exception
            persistence.save(instance_name, project['version'])
        else:
            print 'Error with instance %s. The status is "%s"' % (instance.id, status)
            instance_ids = None
    return instance_ids


def is_running(instance_ids, project):
    if instance_ids is None:
        return False
    else:
        tenant = landlord.Tenant()
        tenant.load_properties()
        connection = ec2.connect_to_region(tenant.get_property('deploy.region'),
                                           aws_access_key_id=tenant.get_property('aws.id'),
                                           aws_secret_access_key=tenant.get_property('aws.secret'))
        instances = connection.get_only_instances(instance_ids)
        for instance in instances:
            if project['type'] == 'play2':
                try:
                    if tenant.get_property('deploy.check.url', 'False') == 'True':
                        check_url(instance.public_dns_name,
                                  tenant.get_property('healthcheck.method', 'GET'),
                                  tenant.get_property('healthcheck.port', '9000'),
                                  tenant.get_property('healthcheck.path', '/public/version.txt'))
                except:
                    return False
            if instance.update() != "running":
                return False
        return True


@retry(wait_random_min=1000, wait_random_max=5000, stop_max_delay=300000)
def check_url(url, method, port, path):
    print "connecting to %s" % url
    conn = httplib.HTTPConnection(url, int(port))
    conn.request(method, path)
    response = conn.getresponse()
    print response.status
    if response.status != 200:
        print "Instance %s : %s" % (url, response.status)
        raise Exception("check_url : Retry failed", "After retrying to connect to the instances, it is still down")



def terminate(instance_ids):
    if len(instance_ids) == 0:
        return False
    else:
        tenant = landlord.Tenant()
        tenant.load_properties()
        connection = ec2.connect_to_region(tenant.get_property('deploy.region'),
                                           aws_access_key_id=tenant.get_property('aws.id'),
                                           aws_secret_access_key=tenant.get_property('aws.secret'))
        return sorted(connection.terminate_instances(instance_ids)) == sorted(instance_ids)


def get_instances(filters={}, region=None):
    tenant = landlord.Tenant()
    tenant.load_properties()

    if region is None:
        region = tenant.get_property('deploy.region')

    conn = ec2.connect_to_region(region,
                                 aws_access_key_id=tenant.get_property('aws.id'),
                                 aws_secret_access_key=tenant.get_property('aws.secret'))
    returned_instances = conn.get_only_instances(filters=dict({'tag:Deployer': 'igor'}.items() + filters.items()))
    return returned_instances


def get_all_instances(region='eu-west-1'):
    instances = []
    returned_instances = get_instances(region=region)
    for instance in returned_instances:
        try:
            name = instance.tags['Name'][instance.tags['Name'].index("-")+1:]
        except:
            name = instance.tags['Name']
        instances.append({'name': name,
                          'version': instance.tags['Version'],
                          'project': instance.tags['Project'],
                          'date': instance.launch_time,
                          'ip': instance.ip_address or "None",
                          'ami': instance.image_id,
                          'status': instance.state})
    return instances