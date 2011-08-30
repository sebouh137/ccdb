import posixpath
import logging
import time

import ccdb
from ccdb.ccdb_pyllapi import Directory, ConstantsTypeTable, ConstantsTypeColumn, Variation
from ccdb import MySQLProvider, TextFileDOM
from ccdb.cmd import ConsoleUtilBase
from ccdb.cmd import Theme
from ccdb.cmd import is_verbose, is_debug_verbose

log = logging.getLogger("ccdb.cmd.utils.add")

#ccdbcmd module interface
def create_util_instance():
    log.debug("      registring AddData")
    return AddData()


#*********************************************************************
#   Class AddData - Add data constants                               *
#                                                                    *
#*********************************************************************
class AddData(ConsoleUtilBase):
    """ Add data constants according given type table"""
    
    # ccdb utility class descr part 
    #------------------------------
    command = "add"
    name = "AddData"
    short_descr = "Add data constants"
    uses_db = True
    d_i = "      "; #debug indent. Dont bother your mind what is this

    #variables for each process
    rawentry = "/"   #object path with possible pattern, like /mole/*
    path = "/"       #parent path
    
#----------------------------------------
#   process 
#----------------------------------------  
    def process(self, args):
        log.debug(self.d_i + "---------------------------------------------")
        log.debug(self.d_i + "AddData is gained a control over the process.")
        log.debug(self.d_i + "args: " + " ".join(args))

        assert self.context != None
        provider = self.context.provider
        isinstance(provider, MySQLProvider)
        
        #set arguments to default
        self.raw_table_path = ""
        self.table_path = ""
        self.raw_file_path = ""
        self.file_path = ""
        self.run_min = 0
        self.run_max = ccdb.INFINITE_RUN
        self.variation = ""
        self.comment = ""
        self.is_namevalue_format = False
        self.no_comments = False
        self.c_comments = False   #file has '//'-style comments

        #process arguments
        if not self.process_arguments(args):
            log.debug(self.d_i + "process arguments " + Theme.Fail + "failed");
            return 1
        
        #by "" user means default variation
        if self.variation == "":
            self.variation = "default"
        
        #validate what we've got
        if not self.validate():
            log.debug(self.d_i + "arguments validation " + Theme.Fail + "failed");
            return 1
        
        #correct paths
        self.table_path = self.context.prepare_path(self.raw_table_path)
        self.file_path = self.raw_file_path
        
        #reading file
        dom = None
        try:
            if not self.is_namevalue_format:
                dom = ccdb.read_ccdb_text_file(self.file_path)
            else:
                dom = ccdb.read_namevalue_text_file(self.file_path, self.c_comments)
        except IOError as error:
            log.warning("Unable to read file %s. The error message is: \n %s"%(self.file_path, error.message))
            return 1  
        
        #check what we've got
        assert isinstance(dom, TextFileDOM)     
        if not dom.data_is_consistant:
            log.warning("Number of columns in rows are inconsisnsant in file")
            return 1
        
        if len(dom.comment_lines):
            self.comment += "\n" + "\n".join(dom.comment_lines)
            
        # >oO debug record
        log.debug(self.d_i+"adding constants")
        log.debug(self.d_i+"columns {0} rows {1} comment lines {2} metas {3}".format(len(dom.rows[0]), len(dom.rows), len(dom.comment_lines), len(dom.metas)))


        #try to create
        result = provider.create_assignment(dom, self.table_path, self.run_min, self.run_max, self.variation, self.comment)
        
        if not result: 
            log.warn("Constants adding " +Theme.Fail+" error "+Theme.Reset)
            return provider.get_last_error()
        
        log.info("Constants added " +Theme.Success+"successfully"+Theme.Reset)
        return 0
            
#----------------------------------------
#   process_arguments 
#----------------------------------------  
    def process_arguments(self, args):
        
        #parse loop
        i=0
        token = ""
        while i < len(args):
            token = args[i].strip()
            i+=1
            if token.startswith('-'):
                #it is some command, lets parse what is the command

                #variation
                if token == "-v" or token.startswith("--variation"):
                    if i<len(args):
                        self.variation = args[i]
                        i+=1
                                                                                    
                #runrange
                if token == "-r" or token == "--runrange":
                    result = self.context.parse_run_range(args[i])
                    i+=1
                    if not result:
                        log.warning("Run range should be in form of: min-max, or min- , or -max")
                        return False
                    
                    #there is a result
                    (self.run_min,  self.run_max, run_min_set, run_max_set) = result
                    
                    #check how the bounds were set
                    if not run_min_set:
                        log.warning("Min run bound was set as 0 by default")
                    if not run_max_set:
                        log.warning("Max run bound was set as INFINITE_RUN by default")
                    
                
                #file
                if token == "-f" or token == "--file":
                    self.rawentry = args[i]
                    self.object_type = "directory"
                    i+=1
                
                #skip comments 'no-comments' value
                if token == "-n" or token == "--no-comments":
                    self.no_comments = true
                
                #name-value file mode
                if token == "--name-value":
                    self.is_namevalue_format = True
                
                #c style comments
                if token == "--c-comments":
                    self.c_comments = True

            else:
                if token.startswith("#"):
                    #everething next are comments
                    self.comment += " ".join( args[i-1:])
                    self.comment.strip()
                    self.comment = self.comment[1:]
                    break #break the loop since everething next are comment
                
                #it probably must be a type table path
                if self.raw_table_path == "":
                    self.raw_table_path = token
                elif self.raw_file_path == "":
                    self.raw_file_path = token
        
        return True
    
    
#----------------------------------------
#   validate 
#----------------------------------------  
    def validate(self):
        if not self.raw_file_path : return False
        if not self.raw_table_path: return False
        return True

    
#----------------------------------------
#   print_help 
#----------------------------------------
    def print_help(self):
        "Prints help of the command"
          
        print """Add data constants according given type table
    add <type table path>  -v <variation>  -r <run_min>-<run_max>  file_to_import

Required parameters:
    <type table path> - must be /absolute/path/ in command line mode
                        might be also relative/path in interactive mode 

    <variation> - variation name 
    
    <run_min>-<run_max> - run range. 
        if one inputs '<run_min>-' this means <run_min>-<infinit run>
        if one inputs '-<run_max>' this means <0>-<run_max> 
        if one omits runrange at all. The data will be put as
    
   file_to_import - file to import. It should be ccdb file format (see documentation or file format section) 
                    if file format is column of names and column of values add --name-value flag

Additionsl flags:
    
          --name-value  - indicates that the input file is in name-value format (column of names and column of values)
    -n or --no-comments - do not add all "#..." comments that is found in file to ccdb database
          --c-comments  - for files that contains '//' - C style comments. The add replaces simply // to #. 
    
    """
