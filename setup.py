from distutils.core import setup

setup(
        name='pyFlightAnalysis',
        version='1.0beta',
        packages=['src','model','icons'],
        license='MIT',
        long_description=open('README.txt').read(),
        install_requires=[
            "pyqtgraph >= 0.10.0",
            "numpy >= 1.0.0",
            "PyOpenGL >= 3.1.0",
            ],
)
