🔥 FayIR 🔥
-----

![Video](https://github.com/muhammet-mucahit/FayIR/blob/master/video/fayir.gif)
-----

### Introduction

FayIR is a project which provides chance to bring musical venues and artists together. You can add a show with an Artist in an Venue and control all of these processes.

### Development Setup

To start and run the local development server,

0. Find config.py file and change Database with yours:

*If you use any database other than Postgres, you have to add your dialect package to **requirements.txt***
  ```
  $ SQLALCHEMY_DATABASE_URI = '<Put your local database url>'
  $ flask db init
  $ flask db migrate
  $ flask db upgrade
  ```
  
1. Initialize and activate a virtualenv:
  ```
  $ cd YOUR_PROJECT_DIRECTORY_PATH/
  $ python3 -m venv venv
  $ source venv/bin/activate
  ```

2. Install the dependencies:
  ```
  $ pip install -r requirements.txt
  ```

3. Run the development server:
  ```
  $ export FLASK_APP=myapp
  $ export FLASK_ENV=development # enables debug mode
  $ python3 app.py
  ```

4. Navigate to Home page [http://localhost:5000](http://localhost:5000)
