#include <stdio.h>
#include <dlfcn.h>

int main() {
    void *handle;
    int (*add_function)(int, int); // Function pointer type

    handle = dlopen("./libmylibrary.so", RTLD_LAZY); // Load the library

    if (!handle) {
        fprintf(stderr, "Error loading library: %s\n", dlerror());
        return 1;
    }

    add_function = (int (*)(int, int))dlsym(handle, "add"); // Get function address

    if (!add_function) {
        fprintf(stderr, "Error getting symbol: %s\n", dlerror());
        dlclose(handle);
        return 1;
    }

    int result = add_function(5, 3); // Call the function
    printf("Result: %d\n", result);

    dlclose(handle); // Unload the library
    return 0;
}
