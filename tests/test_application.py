import sys
from wds.igor.job import Job
import unittest
import application
from flask import request
from flask import Flask
import mock
from mock import Mock
from wds.igor import job


class StubHeaders():
    def get(self, key):
        return "Lol"


def pop_last_call(mock):
    if not mock.call_count:
        raise AssertionError("Cannot pop last call: call_count is 0")
    mock.call_args_list.pop()
    try:
        mock.call_args = mock.call_args_list[-1]
    except IndexError:
        mock.call_args = None
        mock.called = False
    mock.call_count -= 1

class ApplicationTest(unittest.TestCase):

    @mock.patch('application.igor')
    def test_we_can_deploy(self, mock_igor):
        app = Flask(__name__)

        json = {'domain': 'mydomain.net', 'region': 'eu-west-1', 'username': 'root',
                'environment': 'STAGE',
                'keyfile': 'mykeyfile',
                'projects': [{'name': 'project1', 's3_path': 'folder1/project1',
                              'artifact': 'project1-v57.tgz',
                              'version': 'v57', 'type': 'maven',
                              'folder': 'folderName'},
                             {'name': 'project2', 's3_path': 'folder2/project2',
                              'artifact': 'project2-v189.tgz',
                              'version': 'v189', 'type': 'play',
                              'folder': 'folderName'}]}

        with app.test_request_context('/deploy'):
            request.headers.get = Mock(return_value="xxxxxxxxxxxxxxxxxxxxxxxxxxx")
            jobs = [Job(json["projects"][0]), Job(json["projects"][1])]
            job.JobBuilder.build_jobs = Mock(return_value=[jobs[0], jobs[1]])
            request.get_json = Mock(return_value=json)

            application.deploy_function()

            request.headers.get.assert_called_with('X-Igor-Token')
            pop_last_call(request.headers.get)
            request.headers.get.assert_called_with('X-Igor-Token')
            mock_igor.deploy.assert_called_with(jobs[1])
            pop_last_call(mock_igor.deploy)
            mock_igor.deploy.assert_called_with(jobs[0])