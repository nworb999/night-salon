class GracefulExit(SystemExit):
    pass

def handle_shutdown(signum, frame):
    raise GracefulExit()
