import signal
import atexit
from flask import Flask, request, jsonify
from flask_cors import CORS
import serv.semrider as sm
#from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
import uuid

app = Flask(__name__)
CORS(app)
embed_file = "serv/res/embed_prod_v02_rc.pkl"
meta_file = "serv/res/meta_prod_v02_rc.pkl"
sm.load_data(embed_file, meta_file)

# For task_queue
executor = ThreadPoolExecutor(max_workers=1)
tasks = {}


def dump_files(*args):
    #TODO: Track tasks & check if tasks are executing before exiting
    sm.save_data(embed_file, meta_file)
    exit()


@app.route('/update', methods=['POST'])
def update():
    site = request.json.get('site')
    received_text = request.json.get('text')
    #print(f'Received Data: {received_text}')
    #print(f'Received site: {site}')
    print('Size before ', site[:40] , sm.sim_sys.get_size())
    
    # Task Management
    task_id = str(uuid.uuid4())
    task = executor.submit(run_task, task_id, site, received_text)

    # TODO: Add task status if needed
    # tasks[task_id] = task

    print('Size process ', site[:40] , sm.sim_sys.get_size())
    return jsonify({'status': 'success'})


# TODO: Add tasks status if needed
#@app.route('/update/status/<task_id>', methods=['GET'])
#def get_status(task_id):
#    ''' Don't really need this & currently not used in front-end
#         Adding this code, incase this was ever needed
#    ''' 
#    task = tasks.get(task_id)
#    if task is None:
#        return jsonify({'status': 'invalid task_id'}), 404
#    if task.done():
#        return jsonify({'status': 'completed'})
#    return jsonify({'status': 'in progress'})



def run_task(task_id, site, received_text):
  print("RUN TASK: ", site, received_text[:10])
  sm.update(site, received_text)
  return


@app.route('/search', methods=['POST'])
def search():
    question = request.json.get('question')
    number_of_results = int(request.json.get('number_of_results'))
    results = sm.find(question, number_of_results)
    results = {'top_sites': [u for u,t in results], 'top_context': [t for u,t in results]}
    return jsonify(results)


signal.signal(signal.SIGINT, dump_files)


if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, use_reloader=False)
