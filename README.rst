pyFlightAnalysis
================

A tool written by python to visualize the flight log data inspired by
FlightGear. Other log analysis tools see
`dev.px4.io <https://dev.px4.io/advanced-ulog-file-format.html>`__

.. figure:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/gui.png
   :alt: pyFlightAnalysis GUI

   pyFlightAnalysis GUI

Installation
------------

There are two way to run pyFlightAnalysis

Run from source
^^^^^^^^^^^^^^^

pyFlightAnalysis is based on pyqtgraph (which based on PyQt ), pyOpenGL,
pyulog besides generally used scientific packages like numpy, matplotlib
etc. If you have installed these packages. You can download the source
file

.. code:: bash

    # In folder where you want put the source code
    git clone https://github.com/Marxlp/pyFlightAnalysis.git
    cd pyFlightAnalysis
    python analysis.py

Install and Run
^^^^^^^^^^^^^^^

Due to PyQt4 is can't directly installed by pip, so you need install
`PyQt4 <https://riverbankcomputing.com/software/pyqt/download>`__ by
hands. If you use anaconda, it can be installed by
``conda install pyqt``. PyQt5 can install directly from pip but only
support python3.x. After install PyQt, you can

.. code:: bash

    # Install from pypi
    pip install pyFlightAnalysis

    # or install from source
    git clone https://github.com/Marxlp/pyFlightAnalysis.git
    python setup.py install

    # then run it
    analysis

Features
--------

-  Dynamic filter for looking data
-  3D visulization for attitude and position of drone
-  Easily replay with pyqtgraph's ROI (Region Of Interest)

Usage
-----

Video Tutorial:
^^^^^^^^^^^^^^^

`Brief usage tutorial of
pyFlightAnalysis <https://youtu.be/g05gXfujbFY>`__

Literacy Tutorial:
^^^^^^^^^^^^^^^^^^

1. Open log file (currently only support .ulg filemat) by clicked |open
   file|
2. Choose data by using filter |filter data| and double click to add it.
3. Change color or toggle visibility |change color or toggle visibility|
4. Scroll the middle wheel of mouse to zoom, press down and drag to move
   the curve
5. Click |show quadrotor| to show 3D viewer ( currently may not be
   robust)
6. Press |play data| to play ( you'd better open the 3D viewer to show
   the animation)

Issues
------

If you have install PyQt4 and pyqtgraph but with below error

.. code:: bash

    ImportError: cannot import name QtOpenGL

try

.. code:: bash

    sudo apt-get install python-qt4-gl

License
-------

`MIT <https://github.com/Marxlp/pyFlightAnalysis/LICENSE>`__

.. |open file| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/open_file.png
.. |filter data| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/filter_data.png
.. |change color or toggle visibility| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/modify_graph.png
.. |show quadrotor| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/show_quadrotor.png
.. |play data| image:: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/play_data.png

