from datetime import date

db = dict()


def save(project_name, version):
    last_date = None
    last_version = None
    try:
        last_date = db[project_name+'_current_date']
        last_version = db[project_name+'_current_version']
    except KeyError:
        print 'No previous version of project ' + project_name
    db[project_name+'_current_date'] = date.today().isoformat()
    db[project_name+'_current_version'] = version
    db[project_name+'_last_date'] = last_date
    db[project_name+'_last_version'] = last_version


def get(project_name):
    try:
        return {'version': db[project_name+'_current_version'],
                'date': db[project_name+'_current_date'],
                'last_version': db[project_name+'_last_version'],
                'last_date': db[project_name+'_last_date']}
    except KeyError:
        return None


def clear():
    db.clear()