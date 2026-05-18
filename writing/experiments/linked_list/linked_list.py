# let's make a linked list class


class Node:
    def __init__(self, value, next_node=None):
        self.value = value
        self.next_node = next_node


class LinkedList:
    def __init__(self, head=None):
        self.head = head

    def add(self, value):
        new_node = Node(value)
        new_node.next_node = self.head
        self.head = new_node
        return self.head

    def reverse(self):

