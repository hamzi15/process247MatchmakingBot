class Queue():
    def __init__(self):
        self.lst = list()

    def __len__(self):
        return len(self.lst)

    def pop(self):
        return self.lst.pop(0)

    def push(self, object):
        self.lst.append(object)

