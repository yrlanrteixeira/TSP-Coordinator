DEFAULT_CONFIG = {
    'coordinator': {
        'host': 'localhost',
        'port': 8888,
        'max_workers': 10
    },
    'worker': {
        'coordinator_host': 'localhost',
        'coordinator_port': 8888,
        'heartbeat_interval': 5
    },
    'client': {
        'coordinator_host': 'localhost',
        'coordinator_port': 8888
    },
    'timeouts': {
        'connection': 10,
        'heartbeat': 15,
        'task_completion': 60
    }
} 