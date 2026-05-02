from setuptools import setup, find_packages

setup(
    name='quiz-analysis-system',
    version='2.0.0',
    description='学智画像：教育大数据赋能高校学情可视分析系统',
    author='Your Team',
    author_email='your-email@example.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==2.3.3',
        'Flask-SQLAlchemy==2.0.20',
        'Flask-Login==0.6.2',
        'Flask-WTF==1.2.1',
        'torch==2.2.0',
        'pandas==2.2.3',
        'numpy==1.26.4',
        'matplotlib==3.8.3',
        'seaborn==0.13.2',
        'scikit-learn==1.4.1',
        'markupsafe==2.1.3'
    ],
    entry_points={
        'console_scripts': [
            'quiz-system=run:app.run'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8'
)