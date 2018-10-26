from setuptools import setup,find_packages

setup(
        name='pyFlightAnalysis',
        version='1.0.6b2',
        description='Flight log Data analysis visualization tool',
        long_description=open('README.rst').read(),
        url='https://github.com/Marxlp/pyFlightAnalysis',
        author='Marx Liu',
        author_email='smartlazyman@gmail.com',
        license='MIT',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.7',
            ],
        keywords='px4 log analysis',
        packages=['pyflightanalysis'],
        package_dir={'pyflightanalysis':'src'},
        package_data={'pyflightanalysis':['models/*','icons/*']},
        install_requires=[
            "pyqtgraph >= 0.10.0",
            "numpy >= 1.0.0",
            "PyOpenGL >= 3.1.0",
            "pyulog >= 0.5.0",
            ],
        entry_points={
            'console_scripts':[
                'analysis=pyflightanalysis.analysis:main',
                ],
            },
        project_urls={
            'Source':'https://github.com/Marxlp/pyFlightAnalysis',
            },
)
