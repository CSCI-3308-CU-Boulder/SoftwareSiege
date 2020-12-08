> This is a readme Project Team Members: Liam Ryan, Sandeep Kaushik, Evan Clark, Brad Nam, Filip Forejtek

Our project is a tool for project management and team planning. It is simple and far more lightweight than PM platforms like Jira.

Repo organization/structure:

* The "project" folder contains our project code.

* In that directory, the Python files setup the database for our back end. RUN.txt explains in depth this Python code and what dependencies are needed to get it running.

* The "frontend" folder contains the HTML front end for our website.
"index.html" is the main page of our site and the "css" folder contains CSS headers for that and our login page.

Our code is deployed with continuous integration here: http://csci3308-softwaresiege.herokuapp.com/

How to use the website:

* The user can create a login on their very first visit to the website.

* Once logged in, users can add a project task by putting a task title in and pressing enter.

* Other usernames can be mentioned by placing their name in the mention textbox before adding the task.

* Tasks can be completed by clicking on them, which puts a cross through them. (This can be undone by re-clicking them.)

* When a task or project is fully done, and you want it out of the way, hit the delete button to remove them entirely.