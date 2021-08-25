# Flask X-Talk Example

[[_TOC_]]

## Disclaimer
This repository is just an example of a X-Talk based on the Flask Framework. It can not be used directly like an Django reuse app. Of course you can copy any code from it if you think that piece of code is helpful.

## Requirements
* Python 3.6+
* Flask 1.1.1+

## Install
* Clone this repository.
* Go to the repository directory and install the required dependencies:
  ```
  $ pip install -r requirements.txt
  ```

## Configuration
* Go to the `flask-x-talk-example` directory inside the repository.
* Copy the file `.env.example` and name the new one as `.env`.
* Open the `.env` file and fill in the required configurations.
  * This file is an env file which contains a bunch of variables assignments and each variable will be added as an environment variable by the [python-dotenv](https://github.com/theskumar/python-dotenv) package when the server is booted up.
  * The variable assignment is similar to how you declare a variable in a Bash script.

## Reverse Proxy Notes
* If you have use a reverse proxy to do the TLS offloading, the following non-standard HTTP headers must be set:
  * `X-Forwared-For`
  * `X-Forwared-Proto`
  * `X-Forwared-Host`
  * `X-Forwared-Port`

## Start the Server
* Go to the `flask-x-talk-example` directory inside the repository.
* Use the following command to set `FLASK_APP` environment variable:
  ```
  $ export FLASK_APP=main.py
  ```
* Enter the following command to start the server:
  ```
  $ flask run --host {LISTENING_ADDRESS} --port {LISTENING_PORT}
  ```
* Use a browser to browse your website and you will see a page like the following one:
  ![](https://i.imgur.com/sCjvMMm.png)

## Notes
* In this example, the access of an user will be revoked when that user is about to logout. It is not a required procedure, you do not have to do this in your implementation.

## Database Schema
* The following figure shows the database schema used in this example.
  ![](https://i.imgur.com/DBbPCNA.png)

### User Table
* The `sub` field has unique constraint since it is an unique identifier for every user in the IoTtalk Account Subsystem.
* The `username` field does not have unique constraint since a user may delete his/her account and then re-register with the same username, in that case, the username will be the same and that's why the field does not have unique constraint.

### RefreshToken Table
* A refresh token record can associate to multiple access token records since refresh token is only issued by the IoTtalk Account Subsystem when there is no old one or the old one is expired.
