# coding: utf-8
#!/usr/bin/env python
#
# Based on https://pastebin.com/VU2v27bH
# Author: Kirill Vasin

import logging
from time import time
from collections import deque

logger = logging.getLogger(__name__)

class SpamFilter:
    def __init__(self):
        self.limits = {1:3, 5:7, 10:10} # max: 3 updates in 1 second, 7 updates in 5 seconds, 10 updates in 10 seconds
        self.timeout_start = 10
        self.severity = 2
        self.timeouts = {}
        self.times = {}
        self.violations = {}
    def new_message(self, chat_id):
        update_time = time()
        if chat_id not in self.timeouts:
            self.timeouts.update({chat_id: 0})
            self.times.update({chat_id : deque(maxlen=10)})
            self.violations.update({chat_id: 0})
        else:
            if self.timeouts[chat_id] > update_time:
                return 1
            for limit in self.limits:
                amount = 1
                for upd_time in self.times[chat_id]:
                    if update_time - upd_time < limit:
                        amount += 1
                    else:
                        break
                if amount > self.limits[limit]:
                    delta = int(self.timeout_start * self.severity ** self.violations[chat_id])
                    self.timeouts[chat_id] = update_time + delta
                    self.violations[chat_id] += 1
                    logger.warning("User %s is sending too many requests, broke %s limit", chat_id, limit)
                    return "Too many requests. Operations will be availiable in {0}".format(delta) 
        self.times[chat_id].appendleft(update_time)
        return False


    def wrapper(self, func):  # only works on functions, not on instancemethods
        # Only works for messages (+Commands) and callback_queries (Inline Buttons)
        def func_wrapper(bot, update):
            if update.callback_query:
                chat_id = update.callback_query.from_user.id
            elif update.message:
                chat_id = update.message.chat_id
            timeout = self.new_message(chat_id)
            if not timeout:
                return func(bot, update) # return is required by ConversationHandler
            elif timeout != 1:
                bot.sendMessage(chat_id=chat_id, text=timeout)
        return func_wrapper
    
blocker = SpamFilter()

# @blocker.wrapper
# def start(bot, update):
#     ...

