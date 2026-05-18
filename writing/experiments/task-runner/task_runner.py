import threading

TaskID = int


class Task:
    def __init__(self, id: TaskID, depends_on: list[TaskID]):
        self.id = id
        self.depends_on = depends_on
        self.result = None


class ResultQueue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()

    def put(self, result):
        with self.lock:
            self.queue.append(result)

    def get(self):
        with self.lock:
            if self.queue:
                return self.queue.pop(0)
            else:
                return None


class TaskRunner:
    def __init__(self, result_queue: ResultQueue):
        self.tasks = tasks
        self.results = result_queue

    def run(self, tasks: list[Task]):

    def k
