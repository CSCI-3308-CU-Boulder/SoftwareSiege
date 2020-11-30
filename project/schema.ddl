create table Users (uid integer primary key autoincrement , username text unique , email text, password text);
-- due_date is a unix timestamp
create table Projects (pid integer primary key autoincrement, name text, owner int, foreign key (owner) references Users(uid));
-- if you update tasks, you must also update project.html
create table Tasks (tid integer primary key autoincrement , name text, body text, priority integer, due_date integer, added_date integer, project integer, foreign key (project) references Projects(pid));
create table Assignments (atid integer not null, auid integer not null, foreign key(atid) references Tasks(tid), foreign key(auid) references Users(uid));
create table UserProjects (uppid integer not null, upuid integer not null, foreign key(uppid) references Projects(pid), foreign key(upuid) references Users(uid));
create table LS (key text unique not null, body text);