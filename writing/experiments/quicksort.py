import random

list_to_sort: list[int] = [random.randint(0, 100) for _ in range(100)]

def quicksort(list_to_sort: list[int]) -> list[int]:
    if len(list_to_sort) <= 1:
        return list_to_sort

    pivot: int = list_to_sort[0]

    left: list[int] = [x for x in list_to_sort[1:] if x < pivot]
    right: list[int] = [x for x in list_to_sort[1:] if x >= pivot]

    return quicksort(left) + [pivot] + quicksort(right)


if __name__ == "__main__":
    print(f"Before sorting: {list_to_sort}")
    print(f"After sorting: {quicksort(list_to_sort)}")

