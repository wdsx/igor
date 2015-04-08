import unittest

from wds.igor.job import JobBuilder, JobStatus, Job
from mock import Mock
from uuid import uuid4

class JobTest (unittest.TestCase):

    def test_can_create_a_job(self):
        json = {'projects': [{'name': 'project1', 's3_path': 'folder1/project1',
                                                      'artifact': 'project1-v57.tgz',
                                                      'version': 'v57', 'type': 'maven', 'folder': 'folderName'},
                                                     {'name': 'project2', 's3_path': 'folder2/project2',
                                                      'artifact': 'project2-v189.tgz',
                                                      'version': 'v189', 'type': 'play', 'folder': 'folderName'}]}
        jobs = JobBuilder.build_jobs(json)
        self.assertEquals(2, len(jobs))
        self.assertEquals(JobStatus.pending, jobs[0].get_status())
        self.assertEquals(JobStatus.pending, jobs[1].get_status())

        self.assertEquals({'name': 'project1', 's3_path': 'folder1/project1', 'artifact': 'project1-v57.tgz',
                           'version': 'v57', 'type': 'maven', 'folder': 'folderName'}, jobs[0].get_project())
        self.assertEquals({'name': 'project2', 's3_path': 'folder2/project2', 'artifact': 'project2-v189.tgz',
                           'version': 'v189', 'type': 'play', 'folder': 'folderName'}, jobs[1].get_project())

        self.assertTrue(jobs[0].get_id() is not None)
        self.assertTrue(jobs[1].get_id() is not None)

        self.assertNotEqual(jobs[0].get_id, jobs[1].get_id)
        self.assertRegexpMatches(str(jobs[0]), "[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}")
        self.assertRegexpMatches(str(jobs[0]), "[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}")

    def test_we_can_update_the_status_of_a_job(self):
        unit = Job(None)
        self.assertEquals(JobStatus.pending, unit.get_status())
        unit.set_status(JobStatus.done)
        self.assertEquals(JobStatus.done, unit.get_status())
        unit.set_status(JobStatus.failed)
        self.assertEquals(JobStatus.failed, unit.get_status())