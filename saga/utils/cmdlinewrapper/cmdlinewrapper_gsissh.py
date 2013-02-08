
__author__    = "Ole Christian Weidner"
__copyright__ = "Copyright 2012, The SAGA Project"
__license__   = "MIT"

''' Provides a CommandLineWrapper implementation based on simple GSISSH 
    tunneling via a modified pexssh library.
'''

import time
from saga.utils.which import which
from pxgsissh import SSHConnection

class GSISSHCommandLineWrapper(object):

    def __init__(self, host, port, username, userproxies):
        ''' Create a new wrapper instance.
        '''

        if not port : port = 22

        self.host = host
        self.port = port
        self.userproxies = userproxies
        self.username = username

        self._connection = None

    def open(self):
        gsissh_executable = which('gsissh')
        if gsissh_executable is None:
            raise Exception("Couldn't find 'gsissh' executable in path.")

        self._connection = SSHConnection(executable=gsissh_executable, gsissh=True)
        self._connection.login(hostname=self.host, port=self.port,
                               username=self.username, password=None)

    def get_pipe (self) :
        return self._connection.get_pxssh ()

    def close(self):
        self._connection.logout()

    def run_sync(self, executable, arguments, environemnt):
        job_error = None
        job_output = None
        returncode = None

        cmd = executable
        for arg in arguments:
            cmd += " %s " % (arg)

        stderr = "/tmp/saga.cmd.stderr.%d"  %  id(self)
        cmd += " 2>%s"  %  stderr

        t1 = time.time()
        result = self._connection.execute(cmd)
        tdelta = time.time() - t1

        reserr = self._connection.execute("cat %s ; rm %s" %  (stderr, stderr))
        result['error'] = "error: %s" % reserr['output']

        return (cmd, result['output'], result['error'], result['exitcode'], tdelta)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

