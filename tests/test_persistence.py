import unittest
from datetime import date
from wds.persistence import persistence

class PersistenceTest (unittest.TestCase):

    def test_it_saves_and_return_a_value(self):
        unit = persistence
        today = date.today().isoformat()
        unit.save('projectName', 'v2')
        project = unit.get('projectName')
        self.assertEqual(today, project['date'])
        self.assertEqual('v2', project['version'])
        self.assertEqual(None, project['last_version'])
        self.assertEqual(None, project['last_date'])

    def test_it_saves_and_return_a_previous_version(self):
        unit = persistence
        today = date.today().isoformat()
        unit.save('project1', 'v2')
        unit.save('project1', 'v3')
        project = unit.get('project1')
        self.assertEqual(today, project['date'])
        self.assertEqual('v3', project['version'])
        self.assertEqual('v2', project['last_version'])
        self.assertEqual(today, project['last_date'])

    def test_should_return_None_when_getting_non_existing_values(self):
        self.assertEqual(None, persistence.get('non-existing'))

    def test_it_should_keep_the_values_in_several_instances(self):
        persistence.save('project', 'v3')
        project = persistence.get('project')
        self.assertEqual('v3', project['version'])
