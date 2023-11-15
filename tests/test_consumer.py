import requests
from threading import Event
import straders_sdk.request_consumer as rc
import pytest
from datetime import datetime, timedelta


def test_u_singleton():
    """test that the singleton is working"""
    assert rc.RequestConsumer() is rc.RequestConsumer()


def test_u_queue():
    """test that the queue is working"""
    consumer = rc.RequestConsumer(auto_start=False)

    consumer.queue.put(rc.PackageedRequest(0, None, None))
    assert not rc.RequestConsumer().queue.empty()


@pytest.mark.execution_timeout(5)
def test_send_some_requets():
    """test that the queue is working"""
    consumer = rc.RequestConsumer(auto_start=False)
    request = requests.Request("GET", "https://api.spacetraders.io/v2/")
    prepared_request = request.prepare()
    request_1 = rc.PackageedRequest(2, prepared_request, Event())
    request_2 = rc.PackageedRequest(1, prepared_request, Event())
    request_3 = rc.PackageedRequest(0, prepared_request, Event())

    consumer.queue.put((request_1.priority, request_1))
    consumer.queue.put((request_2.priority, request_2))
    consumer.queue.put((request_3.priority, request_3))

    responses = []
    consumer.start()
    while len(responses) < 3:
        if request_1.event.is_set() and 1 not in responses:
            responses.append(1)
        if request_2.event.is_set() and 2 not in responses:
            responses.append(2)
        if request_3.event.is_set() and 3 not in responses:
            responses.append(3)
    consumer.stop()
    assert responses == [3, 2, 1]


@pytest.mark.execution_timeout(5)
def test_send_a_lot_of_requests():
    """test that the consumer is staggering things appropriately"""
    consumer = rc.RequestConsumer(auto_start=False)
    request = requests.Request("GET", "https://api.spacetraders.io/v2/")
    prepared_request = request.prepare()

    start_time = datetime.now()
    many_requests = []
    for i in range(100):
        tupple = (i, rc.PackageedRequest(i, prepared_request, Event()))
        consumer.queue.put(tupple)
        many_requests.append(tupple)
        print(f"request {i} queued")
    consumer.start()
    for i in range(10):
        tupple = (i + 0.5, rc.PackageedRequest(i + 0.5, prepared_request, Event()))
        consumer.queue.put(tupple)
        many_requests.append(tupple)
        print(f"request {i+0.5} queued")
    for tupple in many_requests:
        priority, packaged_request = tupple
        packaged_request: rc.PackageedRequest
        packaged_request.event.wait()
        print(f"request {priority} took {datetime.now() - start_time}")


if __name__ == "__main__":
    test_send_a_lot_of_requests()
