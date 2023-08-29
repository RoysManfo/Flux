from threading import Thread
import time
from typing import List, Callable
import os
import math
import random

# Process status codes
STATUS_OK = 0
STATUS_ERR = 1


class Process:
    def __init__(self, owner: str, command_instance: Callable, line_args: list[str]) -> None:
        self.id: int = None
        self.name: str = line_args[0]
        self.owner: str = owner
        self.command_instance: Callable = command_instance
        self.line_args: List[str] = line_args
        self.started: float = time.time()
        self.status: int | None = None
        self.thread: Thread = None

    def _calculate_time(self, seconds: float) -> str:
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        seconds = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"

        if minutes > 0:
            return f"{minutes}m {seconds}s"

        return f"{seconds}s"

    def run(self):
        self.thread = Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        self.id = self.thread.native_id


    def _run(self):
        self.command_instance.init()
        self.command_instance.run(self.line_args)
        self.command_instance.close()
        self.status = self.command_instance.exit()

    def __str__(self) -> str:
        return f"{self.id}\t{self.owner}\t{self.thread.name}\t{self._calculate_time(self.started - time.time())}"

    def all_info(self) -> str:
        return f"{self.id}\t{self.owner}\t{self.thread.name}\t{self._calculate_time(self.started - time.time())}"


class Processes:
    def __init__(self):
        self.processes: list[Process] = []

    def list(self) -> list:
        # Avoid returning the system managed list of processes
        # Instead return a copy
        return self.processes.copy()
    
    @staticmethod
    def _generate_pid() -> int:
        process_id = os.getpid()
        current_time = int(time.time())
        return int(math.ceil(math.sqrt(process_id * 10 + current_time) * 10) * random.random())


    def add(self, info: object, line_args: List[str], callable: Callable):
        self.processes.append(Process(owner=info.user.username, command_instance=callable, line_args=line_args))
        self.processes[-1].id = self._generate_pid()
        print(f"[{self.processes[-1].id}] {line_args[0]}")
        self.processes[-1].run()
        time.sleep(.1)

    def find(self, id: int) -> Process | None:
        for p in self.processes:
            if p.id == id:
                return p
        return None

    def remove(self, id) -> Process:
        for p in self.processes:
            if p.id == id:
                self.processes.remove(p)
                return p
        return None

    def clean(self) -> None:
        """
        Removes all stoped processes.

        This function is automaticaly called each time the manager handles a command
        """

        for p in self.processes:
            if not p.thread.is_alive():
                self.processes.remove(p)
