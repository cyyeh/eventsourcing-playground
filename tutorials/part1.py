'''
An event-sourced aggregate is persisted by recording the sequence of decisions as a sequence of "events".
This sequence of events is used to reconstruct the current state of the aggregate.

event-sourced aggregates are normally used within an application object, 
so that aggregate events can be stored in a database, and so that aggregates 
can be reconstructed from stored events.
'''
from uuid import UUID

from eventsourcing.application import Application
from eventsourcing.domain import Aggregate, event


class Dog(Aggregate):
    @event('Registered')
    def __init__(self, name):
        self.name = name
        self.tricks = []

    @event('TrickAdded')
    def add_trick(self, trick):
        self.tricks.append(trick)


class DogSchool(Application):
    def register_dog(self, name):
        dog: Dog = Dog(name)
        self.save(dog) # save aggregates
        return dog.id

    def add_trick(self, dog_id, trick):
        dog: Dog = self.repository.get(dog_id) # reconstruct previously saved aggregates
        dog.add_trick(trick)
        self.save(dog)

    def get_dog(self, dog_id):
        dog: Dog = self.repository.get(dog_id)
        return {'name': dog.name, 'tricks': tuple(dog.tricks)}


def test_dog():
    # generating events
    dog = Dog('Fido')
    assert isinstance(dog, Dog)
    assert isinstance(dog, Aggregate)
    assert isinstance(dog.id, UUID)
    assert dog.name == 'Fido'
    assert dog.tricks == []
    dog.add_trick('roll over')
    assert dog.tricks == ['roll over']

    events = dog.collect_events()
    print(events)

    # reconstruct the aggregate
    copy = None
    for e in events:
        copy = e.mutate(copy)
    assert copy == dog


def test_dog_school():
    application = DogSchool()
    dog_id = application.register_dog('Fido')
    application.add_trick(dog_id, 'roll over')
    application.add_trick(dog_id, 'fetch ball')

    dog_details = application.get_dog(dog_id)
    assert dog_details['name'] == 'Fido'
    assert dog_details['tricks'] == ('roll over', 'fetch ball')

    notifications = application.notification_log.select(start=1, limit=10)
    print(notifications)
    assert len(notifications) == 3
    assert notifications[0].id == 1
    assert notifications[1].id == 2
    assert notifications[2].id == 3
    

if __name__ == '__main__':
    test_dog()
    test_dog_school()
