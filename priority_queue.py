import itertools
from heapq import heappush, heappop

# from https://docs.python.org/3/library/heapq.html
# wrapped up into a class
# and tasks are now tuples:
# the zeroth entry is the name, which can be followed by arbitrary extra elements
class PriorityQueue:

    def __init__(self):
        self.pq = []                         # list of entries arranged in a heap
        self.entry_finder = {}               # mapping of task NAMES to entries
        self.counter = itertools.count()     # unique sequence count

    def add_or_update_vertex(self, task, priority):
        'Add a new task or update the priority of an existing task'
        name = task[0]
        # but only update if the priority becomes lower
        if (name in self.entry_finder) and (priority < self.entry_finder[name][0]):
            self.remove_task(task)
        elif (name in self.entry_finder) and (priority >= self.entry_finder[name][0]):
            return
        count = next(self.counter)
        entry = [priority, count, task]
        self.entry_finder[name] = entry
        heappush(self.pq, entry)

    def remove_task(self, task):
        'Mark an existing task as removed.  Raise KeyError if not found.'
        name = task[0]
        entry = self.entry_finder.pop(name)
        entry[-1] = '<removed-task>'

    def pop_vertex(self):
        'Remove and return the lowest priority task. Raise KeyError if empty.'
        while self.pq:
            priority, count, task = heappop(self.pq)
            name = task[0]
            if task != '<removed-task>':
                del self.entry_finder[name]
                return task, priority
        raise KeyError('pop from an empty priority queue')