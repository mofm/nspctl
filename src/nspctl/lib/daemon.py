import os
import signal
import sys
import time
import logging
from .process import pids, Process

logger = logging.getLogger(__name__)


class Daemon(object):
    """
    create your own a subclass Daemon class and override the run() method
    """
    def __init__(self, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.pauseRunLoop = 0
        self.restartPause = 1
        self.waitToHardKill = 3
        self.isReloadSignal = False
        self._canDaemonRun = True
        self.processName = os.path.basename(sys.argv[0])
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr

    def _sigterm_handler(self, signum, frame):
        self._canDaemonRun = False

    def _reload_handler(self, signum, frame):
        self.isReloadSignal = True

    def _makedaemon(self):
        """
        Make a daemon, do double-fork magic.
        """
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent.
                sys.exit(0)
        except OSError as exc:
            logger.error("Fork #1 failed: '{}'".format(exc))
            sys.exit(1)
        # Decouple from the parent environment.
        os.chdir("/")
        os.setsid()
        os.umask(0)
        # Do second fork.
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent.
                sys.exit(0)
        except OSError as exc:
            logger.error("Fork #2 failed: '{}'".format(exc))
            sys.exit(1)
        logger.debug("The daemon process is going to background")
        # Redirect standard file descriptors.
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

    def _getprocess(self):
        procs = []

        for p in pids():
            _proc = Process(p)
            if self.processName in _proc.cmdline():
                if p != os.getpid():
                    procs.append(p)

        return procs

    def start(self):
        """
        Start daemon.
        """
        # Handle signals
        signal.signal(signal.SIGINT, self._sigterm_handler)
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        signal.signal(signal.SIGHUP, self._reload_handler)
        # Check if the daemon is already running.
        procs = self._getprocess()
        if procs:
            pid = ",".join([str(p) for p in procs])
            logger.error("Find a previous daemon processes with PIDs {}".format(pid))
            return False
        else:
            # Daemonize the main process
            self._makedaemon()
            # Start a infinitive loop that periodically runs run() method
            self._infiniteloop()
            logger.debug("Daemon process started successfully")
            return True

    def status(self):
        """
        Get status of the daemon.
        """
        procs = self._getprocess()
        if procs:
            pid = ",".join([str(p) for p in procs])
            return True, pid
        else:
            return False

    def reload(self):
        """
        Reload the daemon.
        """
        procs = self._getprocess()
        if procs:
            for p in procs:
                os.kill(p, signal.SIGHUP)
                logger.debug("Send SIGHUP signal into the daemon process with PID '{}'".format(p))
                return True
        else:
            logger.error("The daemon is not running!")
            return False

    def stop(self):
        """
        Stop the daemon.
        """
        procs = self._getprocess()

        if procs:
            for p in procs:
                os.kill(p, signal.SIGKILL)
                return True
        else:
            logger.error("Cannot find some daemon process, I will do nothing")
            return False

    def restart(self):
        """
        Restart the daemon.
        """
        self.stop()
        if self.restartPause:
            time.sleep(self.restartPause)
        self.start()

        return True

    def _infiniteloop(self):
        try:
            if self.pauseRunLoop:
                time.sleep(self.pauseRunLoop)
                while self._canDaemonRun:
                    self.run()
                    time.sleep(self.pauseRunLoop)
            else:
                while self._canDaemonRun:
                    self.run()
            return True
        except Exception as exc:
            logger.error("Run method failed: {}".format(exc))
            sys.exit(1)

    # this method you have to override
    def run(self):
        pass
