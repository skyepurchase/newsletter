# Newsletter

This is a server and mail agent to run a personal newsletter amongst a group of people. This is a personal hobby which I run for a small number of friend groups.

The main purpose is
1. To get into the habit of being a digital vagabond.
2. To learn more about SQL, CGI, UX, HTTP, encryption, authentication, etc.

## Setup

**This requires a server that supports CGI. I assume CGI scripts are stored in `cgi-bin` folder. Furthermore, that you have set up some CGI workflow.**

**This integrates into my site and some changes will need to be made. In the future I may make this project even more modular with no knowledge of it's surrounding website.**

The entirity of this repository should be placed under the `cgi-bin` folder. There are additional Python scripts which are not included in this repository that sit directly under `cgi-bin` to direct traffic to the relevant function in `cgi.py`.

`requirements.txt` holds all of the python library requirements to run the server. and `cron.sh` should be run via a `cron` agent every week on the day you want to send out reminders.

### SQL

The databases can be instantiated using `init.sql`
```
mysql -h hostname -u user database < path/to/init.sql
```
Assuming you use `mysql`.

A new newsletter can be created with
```
python3 create_newsletter.py --title title --email your_email
```

_Note: you will need to make sure you can automatically send mail from the provided email address. I still use Gmail and so the `mailer.py` script assumes this._

## Running

In theory, after setup this runs automatically with no input from you. Inevitably, there are fires to put out, this very much a work in progress and I **do not actively support this**.
