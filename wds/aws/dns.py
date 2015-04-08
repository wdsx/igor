from boto import route53
from wds.landlord import landlord


def update_dns(dns_name, project, subdomain=None):
    tenant = landlord.Tenant()
    tenant.load_properties()
    conn = route53.connection.Route53Connection(aws_access_key_id=tenant.get_property('aws.id'),
                                                aws_secret_access_key=tenant.get_property('aws.secret'))
    zone_id = get_zone_id(conn.get_hosted_zone_by_name(tenant.get_property('deploy.domain')), tenant.get_property('deploy.domain'))
    records = route53.record.ResourceRecordSets(connection=conn, hosted_zone_id=zone_id)
    register_name = dns_value(tenant.get_property('deploy.domain'), tenant.get_property('environment'), project, subdomain)
    record = route53.record.Record(name=register_name, type="CNAME", resource_records=[dns_name], ttl=300)
    records.add_change_record("UPSERT", record)
    records.commit()


def get_zone_id(aws_response, domain):
    if aws_response is None:
        raise Exception('The domain ' + domain + ' is not registered with AWS')
    # The response is in the format /hostedzone/XXXXXXXX
    zone_id = aws_response.get("GetHostedZoneResponse").get("HostedZone").get("Id").split('/')[2]
    return zone_id


def dns_value(domain, environment, project, subdomain):
        if subdomain is None:
            subdomain = project['name']
        name = "%s.%s.%s" % (subdomain, environment, domain)
        return name.lower()
