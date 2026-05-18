#include <stdio.h>
#include <stdlib.h>

typedef struct node {
    int value;
    struct node *next;
} node;

typedef struct list {
    node *head;
} list;

list *create() {
    list *l = (list *) malloc(sizeof(list));
    l->head = NULL;
    return l;
}

void append(list *l, int value) {
    // create the new node
    node *new_node = (node *) malloc(sizeof(node));
    new_node->value = value;
    new_node->next = NULL;

    // get the start of the list
    node *curr = l->head;

    // replace start if list is empty
    if (curr == NULL) {
        l->head = new_node;
        return;
    }

    // iterate until we find a next pointer that is null
    while (curr->next != NULL) {
        curr = curr->next;
    }
    
    // overwrite the pointer in that location with the new pointer
    curr->next = new_node;
}

void print_list(list *l) {
    node *curr = l->head;
    while (curr != NULL) {
        printf("%d ", curr->value);
        curr = curr->next;
    }
    printf("\n");
}

void reverse_list(list *l) {
    node *curr = l->head;
    node *prev = NULL;
    node *next = NULL;
    // the way to think about this is to "flip the link and then advance"
    // to be able to flip, one must track what came before
    // to advance after flipping, one must track what was in the "next" spot
    while (curr != NULL) {
        next = curr->next;
        curr->next = prev;
        prev = curr;
        curr = next;
    }
    l->head = prev;
}

// create a list of integers from 0 to 10
int main(int argc, char** argv) {
    list* l = create();
    for (int i = 0; i < 10; ++i) {
        append(l, i);
    };
    print_list(l);
    reverse_list(l);
    print_list(l);
}
