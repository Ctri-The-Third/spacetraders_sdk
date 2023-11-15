from datetime import datetime, timedelta
from threading import Event, Thread
from requests import PreparedRequest
from time import sleep
import requests
from queue import PriorityQueue

# this consumer should be a singleton.
# it will have a priority queue of special request objects
# request objects have a priority, a time of addition to the queue, a request object, and an event.

instance = None


class RequestConsumer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, auto_start=True) -> None:
        if hasattr(self, "stop_flag"):
            return
        self.queue = PriorityQueue()
        self.stop_flag = False
        self._consumer_thread = Thread(
            target=self._consume_until_stopped, daemon=auto_start
        )
        self._session = requests.Session()
        if auto_start:
            self.start()
        pass

    def stop(self):
        self.stop_flag = True

    def start(self):
        self.stop_flag = False
        self._consumer_thread.start()

    def _consume_until_stopped(self):
        """this method should be tied to the _consumer_thread"""
        interval = timedelta(milliseconds=60000 / 120)

        while not self.stop_flag:
            if not self.queue.empty():
                next_request = datetime.now() + interval
                tupe = self.queue.get()
                package = tupe[1]
                package: PackageedRequest
                try:
                    # print("Doing the thing")
                    package.response = self._session.send(package.request)

                except Exception as e:
                    print(e)
                if package.response.status_code != 429:
                    package.event.set()
                else:
                    package.priority = 0
                    self.queue.put(0, package)
                sleep(min(0, (next_request - datetime.now()).total_seconds()))
            else:
                sleep(interval.total_seconds())

    def validate(self, response: requests.Response):
        pass


class PackageedRequest:
    def __init__(self, priority: float, request: PreparedRequest, event: Event):
        self.priority = priority
        self.request = request
        self.response = None
        self.event = event
        self.time_added = datetime.now()
