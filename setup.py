try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup
    
    def find_packages():
        """Simple implementation of find_packages"""
        return ['']

setup(
    name="ib-interview-system",
    version="1.0.0",
    description="IB Interview System for scheduling investment banking interviews",
    author="Enrico Pioppi",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask==2.0.1",
        "Werkzeug==2.0.1",
        "PyPDF2==3.0.1",
        "requests==2.26.0",
        "PyJWT==2.8.0",
        "python-dotenv==0.19.0",
        "email-validator==1.1.3",
    ],
    entry_points={
        'console_scripts': [
            'ib-interview=app:app.run',
        ],
    },
) 