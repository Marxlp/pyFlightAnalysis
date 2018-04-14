pyFlightAnalysis
================

A tool written by python to visualize the flight log data inspired by FlightGear. Other log analysis tools see [dev.px4.io](https://dev.px4.io/advanced-ulog-file-format.html)

![pyFlightAnalysis GUI](https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/gui.png)

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
1. Open log file (currently only support .ulg filemat) by clicked ![open file][open_file]
2. Choose data by using filter ![filter data][filter_data]
 and double click to add it.
3. Change color or toggle visibility 
  ![change color or toggle visibility][modify_graph]
4. Scroll the middle wheel of mouse to zoom, press down and drag to move the curve 
5. Click ![show quadrotor][show_quadrotor] to show 3D viewer ( currently may not be robust) 
6. Press ![play data][play_data] to play ( you'd better open the 3D viewer to show the animation)
 
License
-------
[MIT](https://github.com/Marxlp/pyFlightAnalysis/LICENSE)

[open_file]: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/open_file.png
[filter_data]: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/filter_data.png
[modify_graph]: https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/modify_graph.png
[show_quadrotor]:https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/show_quadrotor.png
[play_data]:https://github.com/Marxlp/pyFlightAnalysis/blob/master/images/play_data.png
