pyFlightAnalysis
================

A PX4 flight log (ulog) visual analysis tool, inspired by *FlightPlot*.

.. figure:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/gui.png
   :alt: pyFlightAnalysis GUI

   pyFlightAnalysis GUI
   
*pyFlightAnalysis* is written in Python, and depends on *pyqtgraph* (which is based on *PyQt*), *pyOpenGL*, *pyulog*, and a number of other widely used scientific packages including *numpy*, *matplotlib*, etc. 
   
For other log analysis tools see `dev.px4.io <https://dev.px4.io/advanced-ulog-file-format.html>`__

Installation
------------

You can either clone the repository and run the tool directly from source, or you can install *pyFlightAnalysis* (from source or using the PyPi Python package manager) and then run it. In either case you will first need to install PyQt (as shown below).

Install PyQt
^^^^^^^^^^^^

For *Python 3.x*, PyQt5 can be installed directly from pip:

.. code:: bash

   pip install PyQt5
   
For *Python 2.x*, PyQt can't directly be installed using pip. Instead you will need to `install it manually <https://riverbankcomputing.com/software/pyqt/download>`__ 
(if using Anaconda, install using the command: :code:`conda install pyqt`). 


Run from Source
^^^^^^^^^^^^^^^

After installing PyQt, enter the following commands to install other dependencies:

.. code:: bash

   pip install pyqtgraph pyOpenGL pyulog matplotlib numpy
   
Once you have installed these packages you can clone the source files:

.. code:: bash

   # In folder where you want put the source code
   git clone https://github.com/Marxlp/pyFlightAnalysis.git
   
Then run the *analysis.py* source files:
   
   .. code:: bash

      cd pyFlightAnalysis/src
      python analysis.py

Install and Run
^^^^^^^^^^^^^^^

You can install *pyFlightAnalysis* from either source or PyPi (after first installing PyQt as described above):

.. code:: bash

    # Install from pypi
    pip install pyFlightAnalysis

Or 

.. code:: bash

    # Install from source
    git clone https://github.com/Marxlp/pyFlightAnalysis.git
    python setup.py install

After installing *pyFlightAnalysis* you can run it as shown:

.. code:: bash

    analysis


Features
--------

-  Dynamic filter for displaying data
-  3D visulization for attitude and position of drone
-  Easily replay with pyqtgraph's ROI (Region Of Interest)

Usage
-----

Video Tutorial:
^^^^^^^^^^^^^^^

`Brief usage tutorial of pyFlightAnalysis <https://youtu.be/g05gXfujbFY>`__

Literacy Tutorial:
^^^^^^^^^^^^^^^^^^

1. Open log file (currently only support .ulg format) by clicked |open file|.
2. Choose data by using filter |filter data| and double click to add it.
3. Change color or toggle visibility |change color or toggle visibility|.
4. Scroll the middle wheel of mouse to zoom, press down and drag to move the curve.
5. Click |show quadrotor| to show 3D viewer ( currently may not be robust).
6. Press |play data| to play ( you'd better open the 3D viewer to show the animation).

Issues
------

If you have installed PyQt4 and pyqtgraph but get the error below:

.. code:: bash

    ImportError: cannot import name QtOpenGL

try

.. code:: bash

    >>> sudo apt-get install python-qt4-gl

License
-------

`MIT <https://github.com/Marxlp/pyFlightAnalysis/LICENSE>`__

.. |open file| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/open_file.png
.. |filter data| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/filter_data.png
.. |change color or toggle visibility| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/modify_graph.png
.. |show quadrotor| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/show_quadrotor.png
.. |play data| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/play_data.png

