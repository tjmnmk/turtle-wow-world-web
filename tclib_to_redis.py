#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import threading
import time
import re
import cgi

import redis
import tclib

import config

start = True

class Redis():
    def __init__(self):
        self._redis = redis.StrictRedis(host=config.redis_host, port=config.redis_port, db=config.redis_db)
        self._lock = threading.RLock()

        self._create_max_id()

    def _create_max_id(self):
        if self._get_max_id() is None:
            self._redis.set("max_id", 0)
        
    def save_message(self, msg):
        print msg
        with self._lock:
            max_id = self._get_max_id()
            self._redis.set(max_id + 1, msg, ex=config.redis_ttl)
            self._redis.set("max_id", max_id + 1)
        
    def _get(self, key):
        return self._redis.get(key)
    
    def _get_max_id(self):
        max_id = self._get("max_id")
        if max_id:
            max_id = int(max_id)
        return max_id
    

class TCWorker():
    def __init__(self):
        try:
            self._wow_ver = tclib.WoWVersions(version = config.tc_version)
        except tclib.exceptions.WoWVersionsError as e:
            logging.error(e.message)
            sys.exit(3)

        self._redis = Redis()
            
        self._realmserver = config.tc_realmserver
        self._realmport = config.tc_realmport
        self._realm = config.tc_realm
        self._username = config.tc_username
        self._password = config.tc_password
        self._character = config.tc_character
        self._channel = config.tc_channel
        
        self._status = ""
        self._world = None
        self._connected = False
        
    def run(self):
        self.connect()
        while True:
            try:
                self._world.err()
            except tclib.exceptions.StreamBrokenError as e:
                logging.warning(e.message)
                self._status = "Disconnected"
                self._log_status()
                raise
            time.sleep(1)
                  
    def connect(self):
        self._status = "Connecting"
        r = tclib.Realm(self._username, self._password, self._realmserver, self._realmport, self._wow_ver)
        r.start()
        r.join(60)
        if not r.done():
            self._status = "Unable to connect to Realm List Server; Reconnecting"
            self._log_status()
            r.die()
            return False
        
        try:
            r.err()
        except (tclib.exceptions.LogonChallangeError,
                tclib.exceptions.LogonProofError,
                tclib.exceptions.StreamBrokenError,
                tclib.exceptions.CryptoError) as e:
            self._status = "Unable to connect to Realm List Server; Reconnecting"
            self._log_status()
            logging.debug("%s - %s", type(e), str(e))
            return False
        if self._realm not in r.get_realms():
            self._status = "Realm %s not found" % self._realm
            self._log_status()
            return False
        realm_i = r.get_realms()[self._realm]
        w = tclib.World(realm_i["host"],
                        realm_i["port"],
                        self._username,
                        r.get_S_hash(),
                        self._wow_ver,
                        realm_i["id"],
                        True)
        w.start()
        try:
            players = w.wait_get_my_players()
        except (tclib.exceptions.TimeoutError, tclib.exceptions.StreamBrokenError) as e:
            self._status = "Unable to connect to World Server; Reconnecting"
            self._log_status()
            logging.debug("%s - %s", type(e), str(e))
            w.disconnect()
            return False
            
        try:
            w.login(self._character)
        except tclib.exceptions.BadPlayer as e:
            self._status = "Character %s not found; Reconnecting" % self._character
            self._log_status()
            w.disconnect()
            return False
        
        try:
            w.wait_when_login_complete()
        except (tclib.exceptions.TimeoutError, tclib.exceptions.StreamBrokenError) as e:
            self._status = "Unable to connect to World Server; Reconnecting"
            self._log_status()
            logging.debug("%s - %s", type(e), str(e))
            w.disconnect()
            return False
        w.send_join_channel(self._channel)
        w.callback.register(tclib.const.SMSG_MESSAGECHAT, self._handle_message_chat)
        w.callback.register(tclib.const.SMSG_GM_MESSAGECHAT, self._handle_message_chat)
        self._world = w
        self._status = "Connected"
        self._log_status()
        self._connected = True
        
        return True

    def _parse_itemlink(self, itemlink):
        items = itemlink.split("|")[1:]
        color = cgi.escape(items[0][3:])
        type = cgi.escape(items[1][1:items[1].find(":")])
        id = int(items[1][2 + len(type):items[1].find(":", 3 + len(type))])
        name = cgi.escape(items[2][2:-1])

        return color, type, id, name

    def _wowhead_links(self, msg):
        msg = msg.replace("||", "\0\0")
        for i in range(20):
            start = msg.find("|")
            end = msg.find("|h|r", start + 1) + len("|h|r")
            if start == -1 or end == -1:
                break
            
            try:
                color, type, id, name = self._parse_itemlink(msg[start:end])
            except IndexError:
                break
            link = '<a target="_blank" style="color:#%s" href="http://www.wowhead.com/classic/%s=%d">[%s]</a>' % (color, type, id, name) 
            msg = msg[:start] + link + msg[end:]
        
        msg = msg.replace("|r", "")
        msg = re.sub("\|c[0-9a-fA-F]{8}", "", msg)
            
        msg = msg.replace("\0\0", "|")
        
        return msg
           
    def _log_status(self):
        logging.warning("TC: %s", self._status)
        
    def _handle_message_chat(self, opcode, msg_type, data):
        print data
        if opcode not in (tclib.const.SMSG_MESSAGECHAT,
                          tclib.const.SMSG_GM_MESSAGECHAT):
            return
        if msg_type != tclib.const.CHAT_MSG_CHANNEL:
            return
        if data["channel"].lower() != self._channel.lower():
            return
        
        user = data["source"].name
        msg = data["msg"]
        if user.lower() == self._character.lower():
            return
        
        user = user.decode("utf-8")
        msg = msg.decode("utf-8")

        # msg replace all html tags

        msg = cgi.escape(msg)
        msg = self._wowhead_links(msg)
        print msg

        self._redis.save_message("<b>%s:</b> %s" % (user, msg))

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    
    TCWorker().run()
    
