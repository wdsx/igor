from operator import itemgetter
import sys
from flask import Flask
from flask import abort
from flask import render_template
from flask import send_from_directory
from flask import request
from wds.igor.security import secure
from wds.igor import igor
from wds.logging import log_writer
from wds.igor.job import JobBuilder
from wds.landlord.landlord import Tenant
import ConfigParser

application = app = Flask(__name__)
tenant = Tenant()
tenant.load_properties()


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/deploy", methods=['POST'])
@secure
def deploy_function():
    try:
        for job in JobBuilder.build_jobs(request.get_json()):
            igor.deploy(job)
    except:
        exception = sys.exc_info()[0]
        log_writer.exception("Deployment Error: %s", exception)
        abort(400)
    return "Done"


@app.route("/instances")
def status():
    config = ConfigParser.ConfigParser()
    config.read('igor.ini')
    instances = sorted(sorted(igor.get_instances(), key=itemgetter('name')), key=itemgetter('status'))
    return render_template("status.html", instances=instances,
                           environment=config.get('landlord', 'environment').lower(),
                           domain=tenant.get_property('deploy.domain'))

@app.route('/public/<path:path>')
def send_js(path):
    return send_from_directory('static', path)

@app.route("/ping")
@app.route("/healthcheck")
def healthcheck():
    return "It's alive!!"

@app.route("/stopAutoStopCandidates")
def stop_autostop_candidates():
    igor.stop_auto_stop_candidates()
    return "I've autostopped the candidate instances"

@app.route("/startAutoStartCandidates")
def start_autostart_candidates():
    igor.start_auto_start_candidates()
    return "I've autostarted the candidate instances"

if __name__ == "__main__":
    app.run(debug=True)

