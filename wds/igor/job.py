from enum import Enum
from uuid import uuid4
import types


class JobBuilder():
    @staticmethod
    def build_jobs(json):
        jobs = []
        for project in json["projects"]:
            jobs.append(Job(project))
        return jobs


class Job():
    def __init__(self, project):
        self.__repr__ = self.__str__
        self.id = uuid4()
        self.status = JobStatus.pending
        self.project = project

    def get_id(self):
        return self.id

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status
        if status == JobStatus.failed:
            print "Igor couldn't check if the application [%s] is up. " \
                  "Please check your healthcheck endpoint." % self.project

    def get_project(self):
        return self.project

    def __str__(self):
        return str(self.id)


class JobStatus(Enum):
    failed = 0
    pending = 1
    running = 2
    done = 3