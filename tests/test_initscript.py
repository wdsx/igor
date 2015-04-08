import unittest

from wds.igor import initscript


class InitScriptTest (unittest.TestCase):

    def test_script_is_correct(self):
        project = {}
        project['name'] = 'myProject'
        project['s3_path'] = 's3path'
        project['artifact'] = 'artifact.tgz'
        project['version'] = 'v98'
        project['type'] = "play2"
        environment = 'STAGE'
        script = initscript.Script.get(project, environment).split("\n")
        self.assertEqual(len(script), 2)
        self.assertEquals("#!/bin/bash", script[0].strip())
        self.assertEquals("/home/ec2-user/deploy-scripts/deploy myProject s3path artifact.tgz v98 STAGE play2", script[1].strip())


    def test_script_is_with_play2_when_ignoring_the_build_type(self):
        project = {}
        project['name'] = 'myProject'
        project['s3_path'] = 's3path'
        project['artifact'] = 'artifact.tgz'
        project['version'] = 'v98'
        project['type'] = "play2"
        environment = 'STAGE'
        script = initscript.Script.get(project, environment)
        self.assertTrue("/home/ec2-user/deploy-scripts/deploy myProject s3path artifact.tgz v98 STAGE play2" in script)

    def test_script_is_with_the_build_type_when_we_passed_in(self):
        project = {}
        project['name'] = 'myProject'
        project['s3_path'] = 's3path'
        project['artifact'] = 'artifact.tgz'
        project['version'] = 'v98'
        environment = 'STAGE'
        project['type'] = 'maven'
        script = initscript.Script.get(project, environment)
        self.assertTrue("/home/ec2-user/deploy-scripts/deploy myProject s3path artifact.tgz v98 STAGE maven" in script)
