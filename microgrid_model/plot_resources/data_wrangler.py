from os import getcwd
from tempfile import mkdtemp

from numpy import dump, load

class DataManager(object):
    
    def __init__(self, network, temporary=False, directory=None):
        if temporary is False and directory is None:
            directory = getcwd()
            
        if temporary is True:
            directory = mkdtemp()
            if directory is not None:
                print "Temporary kwarg is True and directory specified, the specified directory will be ignored"
            
        self.save_dir = directory
        
        self.network = network

    
    def dump_all_network_data(self):
        pass

        
    def get_all_network_data(self):
        network_data = []
