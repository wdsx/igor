class Script():

    @staticmethod
    def get(project, environment):
        version = project['version']
        try:
            folder = project['folder']
        except KeyError:
            folder = ""
        if not version.startswith('v'):
            version += 'v'
        script = """#!/bin/bash
        /home/ec2-user/deploy-scripts/deploy %s %s %s %s %s %s %s"""
        return script % (project['name'], project['s3_path'], project['artifact'], version, environment, project['type'], folder)
