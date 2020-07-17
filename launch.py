from services.working_loop import WorkingLoop

try:
    WorkingLoop().start()
except KeyboardInterrupt:
    exit(0)
