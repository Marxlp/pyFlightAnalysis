pyFlightAnalysis
================

A tool written by python languge to visualize the flight log data inspired by FlightGear. Other log analysis tools see [dev.px4.io](https://dev.px4.io/advanced-ulog-file-format.html)

Installation
------------

There are two way to run pyFlightAnalysis

#### Run from source 
pyFlightAnalysis is based on pyQt4,pyqtgraph,pyOpenGL,pyulog except scipy. If you have install these packages. You can download the source file 
```bash
# folder where you want put the source code
git clone https://github.com/Marxlp/pyFlightAnalysis.git
cd pyFlightAnalysis
python analysis.py
```

#### Install and Run
```bash
# Install from pypi
pip install pyFlightAnalysis

# or install from source
git clone https://github.com/Marxlp/pyFlightAnalysis.git
python setup.py install
```

Features
--------
* Dynamic filter for looking data
* 3D visulization for attitude and position of drone
* Easily replay with pyqtgraph's ROI (Region Of Interest)

Usage
-----

#### Video Tutorial:
[Brief usage tutorial of pyFlightAnalysis](https://youtu.be/g05gXfujbFY)

#### Literacy Tutorial:
1. open log file (currently only support .ulg filemat) by clicked ![open file][open_file]
2. choose data by using filter and double click to add it.
  ![filter data][fileter_data]
3. change color or toggle visibility 
  ![change color or toggle visibility][modify_graph]
4. zoom and open the detail graph
  ![zoom and detail][zoom_detail]
5. show 3D viewer ( currently may not be robust) 
  ![3D viewer][3d_viewer] 

License
-------
[MIT](https://github.com/Marxlp/pyFlightAnalysis/LICENSE)
