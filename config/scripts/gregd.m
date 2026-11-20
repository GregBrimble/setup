#import <Foundation/Foundation.h>
#import <dispatch/dispatch.h>
#include <math.h>
#include <stdlib.h>

static NSBackgroundActivityScheduler *activity;
static int runCommand(NSArray<NSString *> *command) {
    @autoreleasepool {
        NSTask *task = [NSTask new];
        task.executableURL = [NSURL fileURLWithPath:command[0]];
        task.arguments = [command subarrayWithRange:NSMakeRange(1, command.count - 1)];
        NSError *error = nil;
        if (![task launchAndReturnError:&error]) {
            NSLog(@"Could not start background command: %@", error);
            return 1;
        }
        [task waitUntilExit];
        if (task.terminationStatus != 0)
            NSLog(@"Background command exited with status %d", task.terminationStatus);
        return task.terminationStatus;
    }
}

int main(void) {
    @autoreleasepool {
        NSArray<NSString *> *args = NSProcessInfo.processInfo.arguments;
        if (args.count == 2 && [args[1] isEqualToString:@"--help"]) {
            puts("gregd ACTIVITY_ID INTERVAL_SECONDS COMMAND [ARG...]\n"
                 "gregd --once COMMAND [ARG...]");
            return 0;
        }
        BOOL once = args.count >= 2 && [args[1] isEqualToString:@"--once"];
        NSUInteger commandIndex = once ? 2 : 3;
        if (args.count <= commandIndex || ![args[commandIndex] isAbsolutePath]) {
            NSLog(@"Provide an absolute command path; use --help for usage.");
            return 64;
        }
        NSArray<NSString *> *command = [args subarrayWithRange:NSMakeRange(commandIndex, args.count - commandIndex)];
        if (once) return runCommand(command);

        double interval = 0;
        NSScanner *scanner = [NSScanner scannerWithString:args[2]];
        if (args[1].length == 0 || ![scanner scanDouble:&interval] || !scanner.isAtEnd || !isfinite(interval) || interval <= 0) {
            NSLog(@"Provide an activity identifier and a positive interval in seconds.");
            return 64;
        }
        activity = [[NSBackgroundActivityScheduler alloc] initWithIdentifier:args[1]];
        activity.repeats = YES;
        activity.interval = interval;
        [activity scheduleWithBlock:^(NSBackgroundActivityCompletionHandler completion) {
            @autoreleasepool {
                if (activity.shouldDefer) {
                    completion(NSBackgroundActivityResultDeferred);
                    return;
                }
                runCommand(command);
                completion(NSBackgroundActivityResultFinished);
            }
        }];
        NSLog(@"Scheduled background activity with macOS: interval %.0f seconds, tolerance %.0f seconds", activity.interval, activity.tolerance);
        dispatch_main();
    }
}
