from sopel import module
import json
import requests
import time
import random
import sqlite3
from urllib.parse import urlparse
from requests_oauthlib import OAuth1

gsEdit = ""

def XMIT(url, payload, method):
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    key1, key2, key3, key4, account = c.execute('''SELECT * from auth where account="Bot873";''').fetchone()
    db.close()
    
    AUTH = OAuth1(key1, key2, key3, key4)
    connect = requests.Session()
    agent = {
        'User-Agent': 'Bot873 v1.2.0 using Sopel (Python3.7)',
        'From': 'contact@873gear.com'
    }
    if method == "post":
        DATA = connect.post(url, headers=agent, data=payload, auth=AUTH).json()
        return DATA
    elif method == "get":
        DATA = connect.get(url, headers=agent, params=payload).json()
        return DATA
    elif method == "authget":
        DATA = connect.get(url, headers=agent, params=payload, auth=AUTH).json()
        return DATA
    else:
        return False

def isGS(nick):
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    GS = c.execute('''SELECT nick from globalsysops;''').fetchall()
    
    GSes = [val for sublist in GS for val in sublist] # Flatten list
    
    if nick in GSes:
        account = c.execute('''SELECT account FROM globalsysops WHERE nick="%s";''' % nick).fetchone()[0]
        db.close()
        return account
    else:
        db.close()
        return False

def getdb(select, table, where, target):
    # Define dbase connection
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    try:
        site = c.execute('''SELECT %s FROM %s WHERE %s="%s";''' % (select, table, where, target)).fetchone()
    except:
        site = None
    
    db.close()
    
    if site is None:
        return None
    else:
        return site

def gsLogin():
    url = "https://meta.wikimedia.org/w/api.php"

    reqtoken = {
        'action':"query",
        'meta':"tokens",
        'format':"json"
    }
    
    DATA = XMIT(url, reqtoken, "authget")
    
    csrf = DATA['query']['tokens']['csrftoken']
    
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    c.execute('''UPDATE config SET csrf_token="%s" where bot_name="GlobalSysBot";''' % csrf)
    
    db.commit()
    db.close()

def gsedit(bot, payload, actName, title): # function to edit on-wiki meta page
    
    # Ditch the stored csrf token and get a new one
    gsLogin()
    
    editSummary = "Automated edit requested via IRC."
    
    editPage = "User_talk:" + actName
    
    csrf = getdb("csrf_token", "config", "bot_name", "GlobalSysBot")
    
    reqEdit = {
        'action':"edit",
        'format':"json",
        'title':editPage,
        'section':"new",
        'sectiontitle':title,
        'text':payload,
        'summary':editSummary,
        'minor':"true",
        'redirect':"true",
        'token':csrf
    }
    
    url = "https://meta.wikimedia.org/w/api.php"
    
    DATA = XMIT(url, reqEdit, "post")

def gsintRun(bot, gswikis, actName): # Alternate form of main function for silently doing the same work.
    gsEdit = ""
    gswikis = gswikis.split(',')
    for project in gswikis:
        gsLinks = ""
        
        try:
            proj, apiurl, csdcat = getdb("*", "GSwikis", "project", project)
        except:
            continue
        
        urlpre = urlparse(apiurl)
        
        gsQuery = {
            'action':"query",
            'format':"json",
            'list':"categorymembers",
            'cmtitle':csdcat
            } # Setup query for MediaWiki API
        
        while True:
            DATA = XMIT(apiurl, gsQuery, "get")
            
            for item in DATA['query']['categorymembers']: # iterate through results
                gshyper = str("#+https://" + urlpre.netloc + "/wiki/" + item['title'] + '+\n')
                gshyperlink = ''.join(gshyper).replace(" ", "_")
                gshyperlink = gshyperlink.replace("+", " ")
                
                if gsLinks == "":
                    gsLinks = "{{Hidden|header=" + project + "|content=" + '\n' + gshyperlink
                else:
                    gsLinks = gsLinks + gshyperlink
                
            if ('continue' not in DATA) or ('error' in DATA):
                break
            
            cont = DATA['continue']
            gsQuery.update(cont)
            
        if gsLinks != "": # conditionally format for page edit
            gsLinks = gsLinks + "}}" + '\n'
            gsEdit = gsEdit + gsLinks
            
    if gsEdit is not "":
        intgreeting = "Hello Global Sysop! I'm delivering your requested daily update. Use <code>!daily del project</code> in {{irc|wikimedia-gs}} to stop these messages."
        intTitle = "Daily Global Sysop Update"
        gsEdit = intgreeting + gsEdit + "~~~~" # finalize edit
        gsedit(bot, gsEdit, actName, intTitle)

def gswork(bot, gswikis, actName): # Main function. Query requested wikis, store resuls
    gsEdit = ""
    gswikis = gswikis.split(' ')
    
    for project in gswikis: # Begin working with each project, 1 by 1
        
        # Check to see if project is known
        try:
            proj, apiurl, csdcat = getdb("*", "GSwikis", "project", project)
        except:
            bot.say("I don't know " + project + "... You can add it by using !add wikiabrev fullAPIurl Category:CSD category. Example: !add enwiki https://en.wikipedia.org/w/api.php Category:Candidates for speedy deletion")
            continue
        
        gsLinks = ""
        urlpre = urlparse(apiurl)
        gsQuery = {
            'action':"query",
            'format':"json",
            'list':"categorymembers",
            'cmtitle':csdcat
        }
        
        while True: # iterate through results
            DATA = XMIT(apiurl, gsQuery, "get")
            
            for item in DATA['query']['categorymembers']:
                gshyper = "#+https://" + urlpre.netloc + "/wiki/" + item['title'] + '+\n'
                gshyperlink = ''.join(gshyper).replace(" ", "_")
                gshyperlink = gshyperlink.replace("+", " ")
                if gsLinks == "":
                    gsLinks = "{{Hidden|header=" + project + "|content=" + '\n' + gshyperlink
                else:
                    gsLinks = gsLinks + gshyperlink
                    
            if ('continue' not in DATA) or ('error' in DATA):
                break
                
            cont = DATA['continue']
            gsQuery.update(cont)
            
        if gsLinks != "": # conditionally format for page edit
            gsLinks = gsLinks + "}}" + '\n'
            gsEdit = gsEdit + gsLinks
            continue
        else:
            bot.say("No items found on " + project)
            gsLinks = ""
            continue
            
    if gsEdit is not "":
        greeting = "Hello friendly Global Sysop! Here is the information you requested..."
        secTitle = "Global Sysop Report for "
        gsEdit = greeting + gsEdit + "~~~~" # finalize edit
        editTitle = secTitle + actName
        gsedit(bot, gsEdit, actName, editTitle)
        bot.say("Request complete! https://meta.wikimedia.org/wiki/User_talk:" + actName)
    else:
        bot.say("No items found so I didn't report to your talk page.")

def gsircwork(bot, wiki, nick): # Do GS work on irc
    try:
        proj, apiurl, csdcat = getdb("*", "GSwikis", "project", wiki)
    except:
        bot.say("I don't know " + wiki + "... You can add it by using !add wikiabrev fullAPIurl Category:CSD category. Example: !add enwiki https://en.wikipedia.org/w/api.php Category:Candidates for speedy deletion")
        return
    
    response = ""
    urlpre = urlparse(apiurl)
    gsQuery = {
        'action':"query",
        'format':"json",
        'list':"categorymembers",
        'cmtitle':csdcat
    }
    
    DATA = XMIT(apiurl, gsQuery, "get")
    
    for item in DATA['query']['categorymembers']:
        response = response + " https://" + urlpre.netloc + "/wiki/" + item['title'].replace(" ", "_")
    
    if response is not "":
        for thing in response.split(' '):
            bot.say(thing)
        bot.say("Request complete.")
    else:
        bot.say("There are no pages listed in the CSD category.")
    
    if 'continue' in DATA:
        bot.say(nick + ", more items exist. Rerun !onirc " + wiki + " after deleting above articles.")

def gsnew(bot, addAbrev, addAPI, addCat): # permit users to add other projects to database
    
    try:
        check = getdb("project", "GSwikis", "project", addAbrev)
    except:
        check = None
    
    if check is not None:
        bot.say("I already know that wiki. If override is needed, contact Operator873")
        return

    else:
        db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
        c = db.cursor()
        
        c.execute('''INSERT INTO GSwikis VALUES ("%s", "%s", "%s");''' % (addAbrev, addAPI, addCat))
        
        db.commit()
        db.close()
                
        bot.say("Project " + addAbrev + " added successfully!")

def gsre(bot, addAbrev, addAPI, addCat): # admin rewrite function. Replace key instead of adding
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    c.execute('''UPDATE GSwikis SET apiurl="%s", csdcat="%s" WHERE project="%s";''' % (addAPI, addCat, addAbrev))
    
    db.commit()
    db.close()
    
    proj, api, csd = getdb("*", "GSwikis", "project", addAbrev)
    
    bot.say("I rewrote " + proj + ". API is " + api + " and CSD cat is " + csd)

def getWiki(bot, project): # debugging func. Returns stored values in database
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    try:
        proj, api, csd = getdb("*", "GSwikis", "project", project)
    except:
        bot.say("I don't think I know " + project)
        return
    finally:
        db.close()
    
    bot.say(proj + " " + api + " " + csd)

@module.require_chanmsg(message="This message must be used in the channel")
@module.commands('update')
@module.nickname_commands('update')
def gsupdate(bot, trigger):
    if trigger.group(2) is None:
        bot.say("Please inlcude a project for me check. Example: !update enwikibooks arcwiki")
    else:
        if isGS(trigger.nick) is not False:
            actName = isGS(trigger.nick)
            abrev = trigger.group(2)
            gswork(bot, abrev, actName)
        else:
            bot.say("I'm sorry! You're not authorized to perform this action.")

@module.require_chanmsg(message="This message must be used in the channel")
@module.commands('add')
@module.nickname_commands('add')
def gsadd(bot, trigger):
    if isGS(trigger.nick) is not False:
        actName = isGS(trigger.nick)
        if trigger.group(2) is None:
            bot.say("Please include wiki abrev, api url, and CSD Category...")
            bot.say("Example: !add test https://test.wikipedia.org/w/api.php Category:Candidates for speedy deletion")
        else:
            try:
                addAbrev, addAPI, addCat = trigger.group(2).split(' ', 2)
            except:
                bot.say("Hmmm... command doesn't look right. Example: '!add simplewiki https://simple.wikipedia.org/w/api/php Category:Quick deletion requests'")
                return
            
            gsnew(bot, addAbrev, addAPI, addCat)
    else:
        bot.say("I'm sorry! You're not authorized to perform this action.")

@module.require_chanmsg(message="This message must be used in the channel")
@module.commands('onirc')
@module.nickname_commands('onirc')
def gsirc(bot, trigger):
    if isGS(trigger.nick) is not False:
        if trigger.group(3) is not None:
            if len(str(trigger.group(2)).split()) > 1:
                bot.say("For IRC responses, only one project is supported. Proceeding with " + trigger.group(3) + ":")
            gsircwork(bot, trigger.group(3), trigger.nick)
        else:
            bot.say("I need a project to check!")
    else:
        bot.say("I'm sorry! You're not authorized to perform this action.")

@module.require_owner(message="This function is only available to Operator873")
@module.commands('idwiki')
def gsid(bot, trigger):
    getWiki(bot, trigger.group(3))

@module.require_owner(message="This function is only available to Operator873")
@module.commands('csrf')
def gscsrf(bot, trigger):
    gslogin()
    csrf = getdb("csrf_token", "config", "bot_name", "GlobalSySBot")[0]
    bot.say(csrf)

@module.require_owner(message="This function is only available to Operator873")
@module.commands('rewrite')
def gsrewrite(bot, trigger):
    addWiki = trigger.group(2)
    try:
        addAbrev, addAPI, addCat = addWiki.split(" ", 2)
        gsre(bot, addAbrev, addAPI, addCat)
    except:
        bot.say("Malformed command. !rewrite <project> <apiurl> <CSD cat>")
        return

@module.commands('randomwiki')
def randomwiki(bot, trigger):
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    list = c.execute('''SELECT project FROM GSwikis;''').fetchall()
    db.close()
    
    limit = len(list)
    rng = random.randint(0,limit)
    bot.say("Random wiki: " + str(list[rng][0]))

@module.require_admin(message="This function is only available to Operator873 and the bot admins.")
@module.commands('authnick')
def authnick(bot, trigger):
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    if isGS(trigger.group(3)) is False:
        nick, account = trigger.group(2).split(' ', 1)
        c.execute('''INSERT INTO globalsysops VALUES ("%s", "%s");''' % (nick, account))
        db.commit()
        db.close()
        bot.say("User " + nick + " added as " + account + " successfully!")
    else:
        bot.say("I already know " + trigger.group(3) + " as " + check)

@module.require_owner(message="This function is only available to Operator873")
@module.commands('idnick')
def idnick(bot, trigger):
    if isGS(trigger.group(3)) is False:
        bot.say("I don't know " + trigger.group(3) + ".")
    else:
        bot.say("I know " + trigger.group(3) + " as " + isGS(trigger.group(3)))

@module.require_owner(message="This function is only available to Operator873")
@module.commands('rmvnick')
def rmvnick(bot, trigger):
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    check = c.execute('''SELECT nick FROM globalsysops WHERE account="%s";''' % trigger.group(2)).fetchall()
    
    if len(check) == 0 or check is None:
        bot.say(trigger.group(3) + " isn't an authorized user.")
    else:
        c.execute('''DELETE FROM globalsysops where account="%s";''' % trigger.group(2))
        db.commit()
        bot.say(trigger.group(2) + " removed from access list.")
    
    db.close()

@module.commands('rmwiki')
@module.require_admin(message="This function is only available to bot administrators")
def rmwiki(bot, trigger):
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    
    try:
        c.execute('''DELETE FROM GSwikis WHERE project="%s";''' % trigger.group(3))
        db.commit()
        bot.say("Successfully removed " + trigger.group(3) + " from database.")
        db.commit()
    except:
        bot.say("Unable to remove " + trigger.group(3) + " from database.")
    finally:
        db.close()

@module.commands('countwikis')
def doCountWikis(bot, trigger):
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()

    try:
        proj = c.execute('''SELECT project FROM GSwikis;''').fetchall()
        count = str(len(proj))
        bot.say("There are currently " + count + " projects in my database.")
    except:
        bot.say("Something bad happened... Operator873 help me.")
    finally:
        db.close()

@module.commands('syncscript')
@module.require_owner(message="This function is only available to Operator873")
def syncwikis(bot, trigger):
    listofwikis = []
    url = "https://meta.wikimedia.org/w/api.php"
    
    agent = {
        'User-Agent': 'Bot873 v1.2.0 using Sopel (Python3.7)',
        'From': 'contact@873gear.com'
    }
    
    getwikis = {
        "action":"query",
        "format":"json",
        "list":"wikisets",
        "wsfrom":"Opted-out of global sysop wikis",
        "wsprop":"wikisnotincluded"
    }
    
    DATA = requests.Session().get(url, headers=agent, params=getwikis).json()
    wikis = DATA['query']['wikisets'][0]
    
    wikilist = wikis['wikisnotincluded']
    
    for wiki in wikilist:
        listofwikis.append(wikilist[wiki])
    
    with open('/home/ubuntu/.sopel/modules/script_template.txt', 'r') as file:
        template = file.read().replace('replaceme', str(listofwikis))
    
    dbdark = sqlite3.connect("/home/ubuntu/.sopel/modules/dark.db")
    dark = dbdark.cursor()
    
    account, key1, key2, key3, key4 = dark.execute('''SELECT * FROM auth WHERE account="Operator873";''').fetchone()
    
    dbdark.close()
    
    AUTH = OAuth1(key1, key2, key3, key4)
    
    reqtoken = {
        'action':"query",
        'meta':"tokens",
        'format':"json"
    }
    
    DATA = requests.Session().get(url, headers=agent, params=reqtoken, auth=AUTH).json()
    
    csrf = DATA['query']['tokens']['csrftoken']
    
    reqEdit = {
        'action':"edit",
        'format':"json",
        'title':"User:Operator873/HideButtonsFromNonGsProjects.js",
        'text':template,
        'summary':"Automated edit... Updating GS wikis",
        'minor':"true",
        'bot':"true",
        'token':csrf
    }
    
    DATA = requests.Session().post(url, headers=agent, data=reqEdit, auth=AUTH).json()
    
    if "error" in DATA:
        errormsg = DATA['error']['info']
        bot.say(errormsg)
    elif "edit" in DATA:
        if DATA['edit']['result'] == "Success":
            bot.say("Done. Non-GS wikis updated.")
    else:
        bot.say("Unknown error occurred! " + str(DATA))
    

@module.commands('newpages')
def getNewpages(bot, trigger):
    DATA = ""
    db = sqlite3.connect("/home/ubuntu/.sopel/modules/wiki2.db")
    c = db.cursor()
    getQuery = {
        "action":"query",
        "format":"json",
        "list":"logevents",
        "leprop":"title|user|timestamp|comment",
        "letype":"create",
        "leaction":"create/create",
        "Fcreate":"",
        "formatversion":"2",
        "lelimit":"4"
    }
    
    getProj = {
        "action":"query",
        "format":"json",
        "meta":"siteinfo",
        "siprop":"general"
    }

    try:
        apiurl, csdcat = c.execute('''SELECT apiurl, csdcat fROM GSwikis WHERE project="%s";''' % trigger.group(3)).fetchall()[0]
    except Exception as e:
        bot.say("I don't know that wiki.")
        db.close()
        return
    finally:
        db.close()
    
    try:
        DATA = XMIT(apiurl, getProj, "get")
        server = DATA['query']['general']['servername']
    except Exception as e:
        bot.say("Ugh... something broke. Help me Operator873! (" + str(e) + ")")
        return
    
    
    DATA = XMIT(apiurl, getQuery, "get")
    for item in DATA['query']['logevents']: # iterate through results
        title = item['title']
        timestamp = item['timestamp']
        user = item['user']
        comment = item['comment']
        link = str("https://" + server + "/wiki/" + title).replace(' ', '_')
        bot.say(timestamp + ": " + user + " created " + link + " with comment: " + comment)

