#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define BUFFER_SIZE 1024

FILE *outputFile = NULL;

void sigint_handler(int signum) {
  printf("Finished measuring CPU usage\n");
  if (outputFile != NULL) {
    fclose(outputFile);
  }
  exit(signum);
}

int main(int argc, char *argv[]) {
  // Registering SIGINT handler
  if (signal(SIGINT, sigint_handler) == SIG_ERR) {
    printf("Failed to register SIGINT handler\n");
    return 1;
  }

  // Check if sleep duration provided as command-line argument
  if (argc != 3) {
    fprintf(stderr, "Usage: %s <sleep_duration_seconds> <output_file>\n",
            argv[0]);
    return 1;
  }

  int sleepDurationSeconds = atoi(argv[1]);
  char *outputFileName = argv[2];

  // Open output file for writing
  FILE *outputFile = fopen(outputFileName, "w");
  if (outputFile == NULL) {
    fprintf(stderr, "Error opening output file\n");
    return 1;
  }

  // Variables to store Unix timestamps
  time_t start_time, end_time;
  struct timespec current_time;

  fprintf(outputFile, "Timestamp,CPU_usage\n");

  fflush(outputFile);
  printf("Started measuring CPU usage\n");

  // Infinite loop to continuously monitor CPU usage
  while (1) {
    // Capture start time
    // start_time = time(NULL);
    // printf("Start Time: %ld\n", start_time);

    // Open /proc/stat file before sleep
    FILE *stat_file_before = fopen("/proc/stat", "r");
    if (stat_file_before == NULL) {
      fprintf(stderr, "Error opening /proc/stat\n");
      return 1;
    }

    // Variables for reading file and parsing CPU statistics before sleep
    char buffer_before[BUFFER_SIZE];
    long long user_before = 0, nice_before = 0, system_before = 0,
              idle_before = 0, iowait_before = 0, irq_before = 0,
              softirq_before = 0, steal_before = 0, guest_before = 0,
              guest_nice_before = 0;

    // Read and parse CPU statistics before sleep
    if (fgets(buffer_before, BUFFER_SIZE, stat_file_before) == NULL) {
      fprintf(stderr, "Error reading /proc/stat\n");
      fclose(stat_file_before);
      return 1;
    }

    sscanf(buffer_before,
           "cpu %lld %lld %lld %lld %lld %lld %lld %lld %lld %lld",
           &user_before, &nice_before, &system_before, &idle_before,
           &iowait_before, &irq_before, &softirq_before, &steal_before,
           &guest_before, &guest_nice_before);

    // Close /proc/stat file
    fclose(stat_file_before);

    // Sleep for specified duration
    usleep(sleepDurationSeconds);

    // Capture end time
    // end_time = time(NULL);
    clock_gettime(CLOCK_REALTIME, &current_time);

    // printf("End Time: %ld\n", end_time);

    // Open /proc/stat file after sleep
    FILE *stat_file_after = fopen("/proc/stat", "r");
    if (stat_file_after == NULL) {
      fprintf(stderr, "Error opening /proc/stat\n");
      return 1;
    }

    // Variables for reading file and parsing CPU statistics after sleep
    char buffer_after[BUFFER_SIZE];
    long long user_after = 0, nice_after = 0, system_after = 0, idle_after = 0,
              iowait_after = 0, irq_after = 0, softirq_after = 0,
              steal_after = 0, guest_after = 0, guest_nice_after = 0;

    // Read and parse CPU statistics after sleep
    if (fgets(buffer_after, BUFFER_SIZE, stat_file_after) == NULL) {
      fprintf(stderr, "Error reading /proc/stat\n");
      fclose(stat_file_after);
      return 1;
    }

    sscanf(buffer_after,
           "cpu %lld %lld %lld %lld %lld %lld %lld %lld %lld %lld", &user_after,
           &nice_after, &system_after, &idle_after, &iowait_after, &irq_after,
           &softirq_after, &steal_after, &guest_after, &guest_nice_after);

    // Close /proc/stat file
    fclose(stat_file_after);

    // Calculate CPU usage percentage
    long long total_before = user_before + nice_before + system_before +
                             idle_before + iowait_before + irq_before +
                             softirq_before + steal_before;
    long long total_after = user_after + nice_after + system_after +
                            idle_after + iowait_after + irq_after +
                            softirq_after + steal_after;

    long long Previdle = idle_before + iowait_before;
    long long Postidle = idle_after + iowait_after;

    long long total_diff = total_after - total_before;
    long long idle_diff = Postidle - Previdle;

    // printf("%lli,%lli\n", total_diff, idle_diff);

    double cpu_usage = 100.0 * (1.0 - (double)idle_diff / total_diff);

    long long end_time =
        current_time.tv_sec * 1000LL + current_time.tv_nsec / 1000000LL;

    // Print CPU usage percentage
    // printf("CPU Usage: %.4f%%\n", cpu_usage);
    // printf("%lli,%lli,%lli,%lli,%lli,%lli,%lli,%lli,%lli,%lli\n",
    // user_before,
    //       nice_before, system_before, idle_before, iowait_before, irq_before,
    //       softirq_before, steal_before, guest_before, guest_nice_before);
    // printf("%lli,%lli,%lli,%lli,%lli,%lli,%lli,%lli,%lli,%lli\n", user_after,
    //       nice_after, system_after, idle_after, iowait_after, irq_after,
    //       softirq_after, steal_after, guest_after, guest_nice_after);

    // printf("%lli,%.4f\n", end_time, cpu_usage);
    // Write timestamp and CPU usage to output file in CSV format
    fprintf(outputFile, "%lli,%.4f\n", end_time, cpu_usage);

    // Flush the output buffer to ensure data is written to file
    fflush(outputFile);
  }

  return 0;
}
