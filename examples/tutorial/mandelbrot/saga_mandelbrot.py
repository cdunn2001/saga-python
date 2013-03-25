import os
import sys
import time
import saga
from PIL import Image

REMOTE_HOST = "alamo.futuregrid.org"

# the dimension (in pixel) of the whole fractal
imgx = 2048 
imgy = 2048

# the number of tiles in X and Y direction
tilesx = 2
tilesy = 2

if __name__ == "__main__":
    try:
        # Your ssh identity on the remote machine
        ctx = saga.Context("ssh")
        ctx.user_id = "oweidner"

        session = saga.Session()
        session.add_context(ctx)

        # list that holds the jobs
        jobs = []

        # create a working directory in /scratch
        dirname = 'sftp://%s/%s/mbrot/' % (REMOTE_HOST, '/tmp')
        workdir = saga.filesystem.Directory(dirname, saga.filesystem.Create,
                                            session=session)

        # copy the executable into our working directory
        mbexe = saga.filesystem.File('sftp://%s/%s/mandelbrot.py' % (REMOTE_HOST, os.getcwd()))
        mbexe.copy(workdir.get_url())

        # the saga job services connects to and provides a handle
        # to a remote machine. In this case, it's your machine.
        # fork can be replaced with ssh here:
        jobservice = saga.job.Service(REMOTE_HOST, session=session)

        for x in range(0, tilesx):
            for y in range(0, tilesy):

                # describe a single Mandelbrot job. we're using the
                # directory created above as the job's working directory
                outputfile = 'tile_x%s_y%s.gif' % (x, y)
                jd = saga.job.Description()
                jd.queue             = "development"
                jd.wall_time_limit   = 10
                jd.total_cpu_count   = 1
                jd.working_directory = workdir.get_url().path
                jd.executable        = 'python'
                jd.arguments         = ['mandelbrot.py', imgx, imgy, 
                                        (imgx/tilesx*x), (imgx/tilesx*(x+1)),
                                        (imgy/tilesy*y), (imgy/tilesy*(y+1)),
                                        outputfile]
                # create the job from the description
                # above, launch it and add it to the list of jobs
                job = jobservice.create_job(jd)
                job.run()
                jobs.append(job)
                print ' * Submitted %s. Output will be written to: %s' % (job.jobid, outputfile)

        # wait for all jobs to finish
        while len(jobs) > 0:
            for job in jobs:
                jobstate = job.get_state()
                print ' * Job %s status: %s' % (job.jobid, jobstate)
                if jobstate is saga.job.Job.Done:
                    jobs.remove(job)
            time.sleep(5)

        # copy image tiles back to our 'local' directory
        for image in workdir.list('*.gif'):
            print ' * Copying %s/%s back to %s' % (workdir.get_url(), image, os.getcwd())
            workdir.copy(image, 'sftp://%s/%s/' % (REMOTE_HOST, os.getcwd()))

        # stitch together the final image
        fullimage = Image.new('RGB', (imgx, imgy), (255, 255, 255))
        print ' * Stitching together the whole fractal: mandelbrot_full.gif'
        for x in range(0, tilesx):
            for y in range(0, tilesy):
                partimage = Image.open('tile_x%s_y%s.gif' % (x, y))
                fullimage.paste(partimage,
                                (imgx/tilesx*x, imgy/tilesy*y,
                                 imgx/tilesx*(x+1), imgy/tilesy*(y+1)))
        fullimage.save("mandelbrot_full.gif", "GIF")
        sys.exit(0)

    except saga.SagaException, ex:
        # Catch all saga exceptions
        print "An exception occured: (%s) %s " % (ex.type, (str(ex)))
        # Trace back the exception. That can be helpful for debugging.
        print " \n*** Backtrace:\n %s" % ex.traceback
        sys.exit(-1)

    except KeyboardInterrupt:
    # ctrl-c caught: try to cancel our jobs before we exit
        # the program, otherwise we'll end up with lingering jobs.
        for job in jobs:
            job.cancel()
        sys.exit(-1)
