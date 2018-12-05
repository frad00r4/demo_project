Demo project
============

Protocol
--------
Protocol is plain text based on JSON
We have got codename, 4 flags and task id
1. Codename is unique name and sets by client and worker for easier
2. Task id is set by client for easier
3. Flags:
    - task_client_request is set by client to dispatcher
    - task_client_response is set by dispatcher to client
    - task_worker_request is set by dispatcher to worker
    - task_worker_response is set by worker to dispatcher

Run
---

python app.py <config_name>

for example:
python app.py worker