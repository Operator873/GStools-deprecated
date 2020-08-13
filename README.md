# GStools

[![GitHub issues](https://img.shields.io/github/issues/Operator873/GStools)](https://github.com/Operator873/GStools/issues)
[![GitHub forks](https://img.shields.io/github/forks/Operator873/GStools)](https://github.com/Operator873/GStools/network)
[![GitHub stars](https://img.shields.io/github/stars/Operator873/GStools)](https://github.com/Operator873/GStools/stargazers)
[![GitHub license](https://img.shields.io/github/license/Operator873/GStools)](https://github.com/Operator873/GStools/blob/master/LICENSE)
![GitHub All Releases](https://img.shields.io/github/downloads/Operator873/GStools/total)
![GitHub contributors](https://img.shields.io/github/contributors/Operator873/GStools)


This is a Sopel IRC Bot module which supports Wikimedia Global Sysops.

The bot functions to assist Global sysops in checking the Category for speedy deletions across any and all Wiki?edia projects. The bot can report those articles found in the categories to an IRC channel or on their talk page at meta.wikimedia.org.

# Dependencies

This module requires Python3.x and libraries: json, requests, time, random, sqlite3, urlparse, and OAuth1.

# WYSIWYG

I'm not a professional programmer. At best, I think of myself as a Python hacker. Everything I write is pretty muched a hack job. If you notice something that could be improved or fixed, please either fix it, or open an issue for me to fix it. Thanks.

# Installation

1. Add the GStools.py and the wiki.db files in /path/to/.sopel/modules/
2. Add "enable = GStools" to /path/to/.sopel/YourBot.cfg
3. Restart your bot.

# Commands

* ```!update project1 project2 project3 ...```
	* Queries the projects and reports the articles listed for quick deletion on your metawiki talk page.

* ```!add project https://some.url Category:The speedy deletion cateogry```
	* Add a new project to the database for future use

* ```!onirc project```
	* Only supports one project at a time to prevent flooding. Reports articles listed for quick deletion in the channel requested.


* ```!idwiki project```
	* Returns the project's api url and category saved in the database.

* ```!csrf```
	* Debug function. Attempts to login to metawiki and obtain a csrf token

* ```!rewrite project```
	* Rewrites the indicated project's api url and category in the database. Useful for correcting typos.

* ```!randomwiki```
	* Selects a random wiki from the database and returns it to the user

* ```!authnick ircNick accountName```
	* Associates the nick with the provided account name and permits access to the commands.

* ```!idnick ircnick```
	* Checks the database for an account associated with the provided IRC nick.

* ```!rmvnick accountName```
	* Removes all IRC nicks associated with the provided account.

* ```!newpages project```
	* Reports first 4 new pages on a project. Useful for tracking spam.
