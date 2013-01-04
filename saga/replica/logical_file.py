

from   saga.task                 import SYNC, ASYNC, TASK, NOTASK
from   saga.url                  import Url
from   saga.replica.constants    import *
from   saga.base                 import Base
from   saga.async                import Async
from   saga.attributes           import Attributes

import saga.exceptions


class LogicalFile (Base, Attributes, Async) :


    def __init__ (self, url=None, flags=READ, session=None, 
                  _adaptor=None, _adaptor_state={}, _ttype=None) : 
        '''
        url:       saga.Url
        flags:     flags enum
        session:   saga.Session
        ret:       obj
        '''

        # param checks
        url     = Url (url)
        scheme  = url.scheme.lower ()

        Base.__init__ (self, scheme, _adaptor, _adaptor_state, 
                       url, flags, session, ttype=_ttype)


    @classmethod
    def create (cls, url=None, flags=READ, session=None, ttype=SYNC) :
        '''
        url:       saga.Url
        flags:     saga.replica.flags enum
        session:   saga.Session
        ttype:     saga.task.type enum
        ret:       saga.Task
        '''

        # param checks
        url     = Url (url)
        scheme  = url.scheme.lower ()

        return cls (url, flags, session, _ttype=ttype)._init_task


    # ----------------------------------------------------------------
    #
    # namespace entry methods
    #
    def get_url (self, ttype=None) :
        '''
        ttype:         saga.task.type enum
        ret:           saga.Url / saga.Task
        '''
        return self._adaptor.get_url (ttype=ttype)

  
    def get_cwd (self, ttype=None) :
        '''
        ttype:         saga.task.type enum
        ret:           string / saga.Task
        '''
        return self._adaptor.get_cwd (ttype=ttype)
  
    
    def get_name (self, ttype=None) :
        '''
        ttype:         saga.task.type enum
        ret:           string / saga.Task
        '''
        return self._adaptor.get_name (ttype=ttype)
  
    
    def is_dir_self (self, ttype=None) :
        '''
        ttype:         saga.task.type enum
        ret:           bool / saga.Task
        '''
        return self._adaptor.is_dir_self (ttype=ttype)
  
    
    def is_entry_self (self, ttype=None) :
        '''
        ttype:         saga.task.type enum
        ret:           bool / saga.Task
        '''
        return self._adaptor.is_entry_self (ttype=ttype)
  
    
    def is_link_self (self, ttype=None) :
        '''
        ttype:         saga.task.type enum
        ret:           bool / saga.Task
        '''
        return self._adaptor.is_link_self (ttype=ttype)
  
    
    def read_link_self (self, ttype=None) :
        '''
        ttype:         saga.task.type enum
        ret:           saga.Url / saga.Task
        '''
        return self._adaptor.read_link_self (ttype=ttype)
  
    
    def copy_self (self, tgt, flags=None, ttype=None) :
        '''
        tgt:           saga.Url
        flags:         enum flags
        ttype:         saga.task.type enum
        ret:           None / saga.Task
        '''

        # ------------------------------------------------------------
        # parameter checks
        tgt_url = Url (tgt)  # ensure valid and typed Url


        # async ops don't deserve a fallback (yet)
        if ttype != None :
            return self._adaptor.copy_self (tgt_url, flags, ttype=ttype)


        try :
            # we have only sync calls here - attempt a normal call to the bound
            # adaptor first (doh!)
            ret = self._adaptor.copy_self (tgt_url, flags, ttype=ttype)
        
        except saga.exceptions.SagaException as e :
            # if we don't have a scheme for tgt, all is in vain (adaptor
            # should have handled a relative path...)
            if not tgt_url.scheme :
                raise e

            # So, the adaptor bound to the src URL did not manage to copy the file.
            # If the tgt has a scheme set, we try again with other matching file 
            # adaptors, by setting (a copy of) the *src* URL to the same scheme,
            # in the hope that other adaptors can copy from localhost.
            #
            # In principle that mechanism can also be used for remote copies, but
            # URL translation is way more fragile in those cases...
            
            # check recursion guard
            if self._is_recursive :
                self._logger.debug("fallback recursion detected - abort")
              
            else :
                # activate recursion guard
                self._is_recursive += 1

                # find applicable adaptors we could fall back to, i.e. which
                # support the tgt schema
                adaptor_names = self._engine.find_adaptors
                ('saga.replica.LogicalFile', tgt_url.scheme)

                self._logger.debug("try fallback copy to these adaptors: %s" % adaptor_names)

                # build a new src url, by switching to the target schema
                tmp_url        = self.get_url ()
                tmp_url.scheme = tgt_url.scheme

                for adaptor_name in adaptor_names :
                  
                    try :
                        self._logger.info("try fallback copy to %s" % adaptor_name)

                        adaptor_instance = self._engine.get_adaptor ('adaptor_name')

                        # get an tgt-scheme'd adaptor for the new src url, and try copy again
                        adaptor = self._engine.bind_adaptor (self, 'saga.replica.LogicalFile', \
                                                             tgt_url.scheme, NOTASK, adaptor_instance)
                        tmp     = saga.replica.LogicalFile (tmp_url, READ, self._session, _adaptor=adaptor)

                        ret = tmp.copy_self (tgt_url, flags)

                        # release recursion guard
                        self._is_recursive -= 1

                        # if nothing raised an exception so far, we are done.
                        return 


                    except saga.exceptions.SagaException as e :

                        self._logger.info("fallback failed: %s" % e)

                        # didn't work, ignore this adaptor
                        pass

            # if all was in vain, we rethrow the original exception
            self._is_recursive -= 1
            raise e
  
    
    def link_self (self, tgt, flags=None, ttype=None) :
        '''
        tgt:           saga.Url
        flags:         enum flags
        ttype:         saga.task.type enum
        ret:           None / saga.Task
        '''
        return self._adaptor.link_self (tgt, flags, ttype=ttype)
  
    
    def move_self (self, tgt, flags=None, ttype=None) :
        '''
        tgt:           saga.Url
        flags:         flags enum
        ttype:         saga.task.type enum
        ret:           None / saga.Task
        '''
        return self._adaptor.move_self (tgt, flags, ttype=ttype)
  
    
    def remove_self (self, flags=None, ttype=None) :
        '''
        flags:         flags enum
        ttype:         saga.task.type enum
        ret:           None / saga.Task
        '''
        return self._adaptor.remove_self (flags, ttype=ttype)
  
    
    def close (self, timeout=None, ttype=None) :
        '''
        timeout:       float
        ttype:         saga.task.type enum
        ret:           None / saga.Task
        '''
        return self._adaptor.close (timeout, ttype=ttype)
  
    
    url  = property (get_url)   # saga.Url
    cwd  = property (get_cwd)   # string
    name = property (get_name)  # string



    # ----------------------------------------------------------------
    #
    # replica methods
    #
    def is_file_self (self, ttype=None) :
        '''
        ttype:    saga.task.type enum
        ret:      bool / saga.Task
        '''
        return self._adaptor.is_file_self (ttype=ttype)

  
    def add_location (self, name, ttype=None) :
        '''
        name:           saga.Url
        ttype:          saga.task.type enum
        ret:            None / saga.Task
        '''
        return self._adaptor.add_location (name, ttype=ttype)


    def remove_location (self, name, ttype=None) :
        '''
        name:           saga.Url
        ttype:          saga.task.type enum
        ret:            None / saga.Task
        '''
        return self._adaptor.remove_location (name, ttype=ttype)


    def update_location (self, old, new, ttype=None) :
        '''
        old:            saga.Url
        new:            saga.Url 
        ttype:          saga.task.type enum
        ret:            None / saga.Task
        '''
        return self._adaptor.update_location (old, new, ttype=ttype)


    def list_locations (self, ttype=None) :
        '''
        ttype:          saga.task.type enum
        ret:            list [saga.Url] / saga.Task
        '''
        return self._adaptor.list_locations (ttype=ttype)


    def replicate (self, name, flags=None, ttype=None) :
        '''
        name:           saga.Url
        flags:          flags enum
        ttype:          saga.task.type enum
        ret:            None / saga.Task
        '''
        return self._adaptor.replicate (name, flags, ttype=ttype)
    

    def upload (self, name, tgt="", flags=None, ttype=None) :
        '''
        name:           saga.Url
        tgt:            saga.Url
        flags:          flags enum
        ttype:          saga.task.type enum
        ret:            None / saga.Task
        '''
        return self._adaptor.replicate (name, flags, ttype=ttype)
    
  
    def download (self, name, src="", flags=None, ttype=None) :
        '''
        name:           saga.Url
        src:            saga.Url
        flags:          flags enum
        ttype:          saga.task.type enum
        ret:            None / saga.Task
        '''
        return self._adaptor.replicate (name, flags, ttype=ttype)
    
  
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

