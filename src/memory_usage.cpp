// Alternative way of obtaining memory data. To be called from app via ctypes.
#include <windows.h>
#include <psapi.h>


extern "C" {
    __declspec(dllexport) int get_memory_usage(DWORD pid);
}


// Returns the working set size in bytes of a given process by ID.
int get_memory_usage(DWORD pid) {
    PROCESS_MEMORY_COUNTERS pmc;

    HANDLE process = OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (process == NULL) {
        // Process not found.
        return -1;
    }
    int memory_usage;
    if (GetProcessMemoryInfo(process, &pmc, sizeof(pmc))) {
        memory_usage = pmc.WorkingSetSize;
    } else {
        // Failed to get process memory data...
        memory_usage = -1;
    }

    CloseHandle(process);
    return memory_usage;
}
