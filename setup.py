from distutils.core import setup

setup(
        name='pyFlightAnalysis',
        version='1.0beta',
        description='Flight log Data analysis visualization tool',
        long_description=open('README.md').read(),
        url='https://github.com/Marxlp/pyFlightAnalysis',
        author='Marx Liu',
        author_email='smartlazyman@gmail.com',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.7',
            ],
        keywords='px4 log analysis',
        packages=['src'],
        install_requires=[
            "pyqtgraph >= 0.10.0",
            "numpy >= 1.0.0",
            "PyOpenGL >= 3.1.0",
            ],
        entry_points={
            'console_scripts':[
                'analysis=pyFlightAnalysis.analysis:main',
                ],
            },
        project_urls={
            'Source':'https://github.com/Marxlp/pyFlightAnalysis',
            },
)
