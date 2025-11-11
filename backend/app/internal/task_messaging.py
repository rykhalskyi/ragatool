class TaskMessenger:
    def __init__(self):
        self.messages = {}

    def send_message(self, task_id: str, message: str):
        if task_id not in self.messages:
            self.messages[task_id] = []
        self.messages[task_id].append(message)

    def get_messages(self, task_id: str):
        return self.messages.get(task_id, [])

task_messenger = TaskMessenger()
