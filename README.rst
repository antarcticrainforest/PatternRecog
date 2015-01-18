Recognition of coastal precipitation
++++++++++++++++++++++++++++++++++++

This repository contains source-code for the recognition of coastal rainfall 
project.

For more details, see the scientific publication 
`Global recognition and analysis of coastline associated rainfall using objective pattern recognition
<doi://XXXXX>`_.

It includes these modules and configuration files:

 * Pattern - python module to run apply the pattern recognition
 * Submit  - python module to submit the recognition jobs to a linux cluster
 * config  - configuration file to run the pattern recognition
 * setup   - text file that defines the threshold combinations to create
   a threshold ensemble

Prerequisites
=============

`Python 2.7 Release <http://www.python.org/>`_ is needed to run the code.

Additionally the following python packages must be installed on the system
to run the pattern recognition:

 * `Numpy <http://www.numpy.org/>`_
 * `SciPy <http://scipy.org/>`_
 * `OpenCV <http://opencv.org/>`_
 * `Netcdf4-Python <http://netcdf4-python.googlecode.com>`_

All packages are open source and should be available via the package manager of
your OS.

To install the packages for Ubuntu 12.04 and later, and Debian wheezy and later::

   apt-get install python-numpy python-scipy python-opencv python-netcdf

On Arch 2012.07.15 and later::
  
  pacman -S python2-numpy python2-scipy opencv
  python2-netcdf4 (via AUR)

On Mac OS X 10.6 and later (via port reposetory system)::
   
   port install py27-numpy py27-scipy py27-netcdf4 opencv +python27

The code expects ``daily`` rainfall input files in netcdf format. As long as it
is sub-daily the temporal resolution doesn't matter. Also any spatial resolution
can be used to run the code. 

You will also need to supply a land-sea mask in netcdf format. 
This mask has to have the same spatial resolution as the rainfall 
estimates and is supposed to be a 2D-array (latlon).

If you wish to create an ensemble of different threshold setups you might want
to take a look into the ``setup`` file. Here all possible threshold combinations
are defined. You can change, delete or add definitions. But note that the names
of each definition should start with ``config`` followed by a 2 digit integer 
such as config01.

For the application of the rainfall threshold a climatology of monthly mean rain 
data is needed. Therefore a multi year monthly mean in a netcdf file should be
created form the rainfall data. Note that unit MUST be the same as for the 
rainfall estimates. For instance we are looking for a monthly average of 3hly
rainfall data and not for a monthly average of daily rainfall data.


Building
========
Additional building should not be necessary


Usage
=====
The pattern recognition can be used in two ways::
 * in single threading mode
 * in multithreading mode via parallel batch system (pbs)

Regardless of the mode you are running the code you will have to edit the file
config. This file provides all necessary parameters to run the code. The
following variables are set:
  
 * folder = the directory of the rainfall estimates.
   The data must have the following structure: ``folder/YYYY/product-YYYY_MM_DD.nc``.
   If folder is set to ``/srv/data/rain/`` and the rainfall product is
   called ``Cmoprh`` the data is expected to have the following structure:
   ``/mnt/data/rain/1998/Cmorph-1998_01_01.nc`` for the 01. Jan 1998.

 * head = the leading string of all filenames, usually the rainfall product
   name
 * targetdir = the directory where the pattern recognition data is stored
 * slmfile   = the filename of the land-sea mask in netcdf-format
 * ensemble  = should be a threshold setup ensemble be created (boolean)
 * reso      = the spatial resolution of the data in km
 * area      = the threshold that is supposed to be meso-scale 
   usually 500 km but you can change it.
 * ecce      = the threshold for eccentricity (see publication for details)
 * beam      = the threshold for the straight length variation
 * perc      = the threshold for the rain intensity in percentiles
 * NOTE: If you choose to create a threshold ensemble the variables ecce, beam, prec
   have no effect.
 * monmean   = netcdf file where a climatology for monthly mean rainfall data
   is stored.
 * erase      = The pattern detection can operate more successfully when small 
   islands are erased from the slm-data.  Should this be done (boolean). 
   Note: tha  this feature is available but not very well tested
 * size       = If erase is set to true what is the maximum size of 
   islands that should be deleted (km^2)
 * scale     = how many boxes representing the coastal area (boxcounting)
 * varname   = the name of the rainfall variable in the netcdf-file
 * lon       = the name of the longitude variable in the netdf-file
 * lat       = the name of the latitude variable in the netcdf-file
 * time      = the name of the time variable in the netcdf-file
 * units     = the unit of the rainfall estimates
 * name      = your name
 * institution = the name of your institution

The module that reads the configuration is written in a way that you can add
any variable you want to the config file. It simply has to have the following
structure::

 key = value

Running in the single mode
--------------------------
If you want to run the pattern recognition in single processing mode simply run
the Pattern script with the following command line options::

 Pattern FirstDate LastDate configXX

Where FirstDate is the starting data and LastData the last date. Note that the 
dates have to be in YYYY-MM-DD format. 

The config parameter is optional and only used if you want to create a threshold
ensemble. the configXX value must be defined in the ``setup`` file.

Note: You you are using a config parameter the ``targetdir`` variable is changed
accordingly. So if you set ``config01`` as config parameter and set 
``/srv/data/PatternDetect/`` as targetdir variable ``Config01`` will be added to the 
targetdir string.

Examples::

   1) Pattern 1998-01-01 2012-12-31 config13
   2) Pattern 1998-01-01 2012-12-31

1) Run the pattern recognition between 01. Jan 1998 and 31. Dec 2012 for threshold
setup ``config13`` as defined in the ``setup`` file. 

2) Same as 1) but without a threshold ensemble.

For more information run::
   
   Pattern --help

Running in paralell mode (PBS)
------------------------------
It is also possible to send several pattern recognition jobs to a Linux cluster
to speed up the process of the recognition.

In general there are two scenarios:

 * distribution of jobs to create a threshold ensemble
 * distribution of jobs between dates

If you choose to create a threshold ensemble and want to distribute the jobs
simply run::

   submit --config=config01,config02,...,configNN FirstDate LastDate

If you don't want to create a threshold ensemble but yet want to send the job 
to a Linux cluster simply run::

   submit FirstDate LastDate

Note the FirstDate and LastDate have the same meaning and format as in running
in single mode

Please type::

   submit --help

to get more info like the maximum number of jobs that are submitted to the 
linux cluster.


If you want to change the header string of the PBS script or change the 
submit command (e.g. to llsubmit) please edit the source-code of submit. 
Header and submit command are defined in the very beginning of the script.


Testing
=======

Some fake rain data with a land-sea mask is comes with the code. The data is
stored in .test in this directory. If you want to test the pattern recognition
simply run::

   Pattern --test


Contributing
============

We welcome all types of contributions, from blueprint designs to
documentation to testing to deployment scripts.


Bugs
====

Bugs should be filed to **martin.bergemann@monash.edu**
