from natural_events_tracker import (
    MAIN_URL,
    GetDataError,
    Event,
    EventTracker,
    TooManyCatError,
)
import pytest


def test_event_attributes():
    event = Event("severestorms", [-10.2, 20.3], [-15.0, 25.5], [2.0, 4.5])
    assert event.x == [-10.2, 20.3]
    assert event.y == [-15.0, 25.5]
    assert event.value == [2.0, 4.5]


def test_event_category_setter():
    event = Event("severestorms", [10, 20], [15, 25], [2, 4])
    event.category = "tsunami"
    assert event.category == "tsunami"


def test_event_attribute_setters():
    event = Event("severestorms", [10, 20], [15, 25.2], [2, 4])
    event.x = [11.23, 21.2]
    event.y = [16.43, 26.2]
    event.value = [3, 5]
    assert event.x == [11.23, 21.2]
    assert event.y == [16.43, 26.2]
    assert event.value == [3.0, 5.0]


def test_get_events():
    event_tracker = EventTracker()
    events = event_tracker.get_events()
    assert all(isinstance(event, Event) for event in events)
    event_tracker = EventTracker(days=30)
    events = event_tracker.get_events()
    assert all(isinstance(event, Event) for event in events)


def test_get_classified_events():
    event_tracker = EventTracker()
    classified_events = event_tracker.get_classified_events()
    for category, events in classified_events.items():
        assert len(events) == sum(
            event.category == category for event in event_tracker.events
        )


def test_get_data():
    et = EventTracker()
    assert isinstance(et.get_data(MAIN_URL), dict)
    with pytest.raises(GetDataError):
        et.get_data("wrong_url")


def test_create_events():
    event_tracker = EventTracker()
    data = event_tracker.get_data(MAIN_URL)
    assert isinstance(event_tracker.create_events(data["events"]), list)
    assert isinstance(event_tracker.create_events(data["events"])[0], Event)


def test_get_classified_events_empty():
    event_tracker = EventTracker()
    event_tracker.events = []
    assert event_tracker.get_classified_events() == {}


def test_classified_events_categories():
    event_tracker = EventTracker()
    unique_categories = set([event.category for event in event_tracker.events])
    assert len(unique_categories) == len(event_tracker.classified_events)


def test_classified_events_events_per_category():
    event_tracker = EventTracker()
    for category, events in event_tracker.classified_events.items():
        assert len(
            [event for event in event_tracker.events if event.category == category]
        ) == len(events)


def test_get_classified_events_raises_error_too_many_cat():
    event_tracker = EventTracker()
    event_tracker.events = [Event(str(i), [], [], []) for i in range(9)]
    with pytest.raises(TooManyCatError):
        event_tracker.get_classified_events()


def test_normalise_events_values_returns_correct_output():
    event_tracker = EventTracker()
    values = [1, 2, 3, None, 5]
    new_values = event_tracker.normalise_events_values(values)
    assert len(new_values) == len(values)
    assert all(20 <= value <= 420 for value in new_values)


def test_calc_dist_returns_correct_output():
    event_tracker = EventTracker()
    x1, y1, x2, y2 = 5, 5, 1, 2
    assert event_tracker.calc_dist(x1, y1, x2, y2) == 5
