# coding: utf-8
import tweepy
import traceback
import sqlite3
import time

#データベース接続
conn = sqlite3.connect('responceList.sqlite3')

#twitter認証
CK = ""
CS = ""
AT = ""
AS = ""

# your bot's name
botsname = "@foo"

auth = tweepy.OAuthHandler(CK, CS)
auth.set_access_token(AT, AS)
api = tweepy.API(auth)


class Listener(tweepy.StreamListener):
    teacher_name=""
    user_word=""
    count=0
    answer_num=0
    sql = "select count(*) from responce;"
    ret = conn.execute(sql)
    rows = ret.fetchall()
    subjectCount=rows[0][0]
    plese_answer=[u"どう答えれば良いのかわかりません", u"どう返答するのが望ましいですか",u"どう返せばいいの？"]
    reply_answer=[u"覚えました", u"わかりました",u"ok"]

    def on_status(self, status):
        try:
            print('------------------------------')
            print(status.text)
            print(u"{name}({screen}) {created} via {src}\n".format(
                name=status.author.name, 
                screen=status.author.screen_name,
                created=status.created_at,
                src=status.source))
            self.DB_operation(status)
        except tweepy.error.TweepError as te:
            text = u"エラーです。結構前に同じことを言っています。"+unicode(int(time.time()))
            api.update_status(status = text)
        except :
            traceback.print_exc()
        return True
     
    def on_error(self, status_code):
        print('Got an error with status code: ' + str(status_code))
        return True
     
    def on_timeout(self):
        print('Timeout...')
        return True

    def DB_operation(self, status):
        #botあての返信かどうか
        word = self.extact_reply_word(status)
        if word == "":
            self.reaction_word(status)
            return 
        else:
            screen_name = status.user.screen_name
            if self.teacher_name == "":
                reply = self.search_from_DB(word)
                self.reply_word(reply, word, screen_name,status.id)
            else:
                self.learn_word(word, screen_name,status.id)


    def extact_reply_word(self,status):
        word = ""
        splitToken = botsname+" "
        tweet_part = status.text.split(splitToken)
        if status.in_reply_to_screen_name == botsname or len(tweet_part) != 1:
            if len(tweet_part) != 1:
                word = tweet_part[len(tweet_part)-1]
            else:
                word = tweet_part[0]
        return word

    def search_from_DB(self, word):
        print word
        sql = "select bot_word from responce where '"+word+"' = user_word;"
        print sql
        ret = conn.execute(sql)
        rows = ret.fetchall()
        if rows == []:
            return ""
        print rows[0]
        return rows[0][0]

    def reply_word(self,reply,word,screen_name,status_id):
        if reply =="":
            text = u"@"+screen_name+u" "+screen_name+u"さん。"+self.plese_answer[self.answer_num] +u"\n現在の登録件数は"+unicode(self.subjectCount)
            self.answer_num +=1
            if self.answer_num == 3:
                self.answer_num=0
            
            api.update_status(status = text,in_reply_to_status_id=status_id)
            self.user_word = word
            self.teacher_name = screen_name
            print "reply_word:"+self.user_word

        else:
            text =u"@"+screen_name+u" "+reply
            api.update_status(status = text,in_reply_to_status_id=status_id)
        print text

    def learn_word(self,bot_word, screen_name,status_id):
        if self.teacher_name == screen_name:
            sql =u"insert into responce values('" +self.user_word+u"','"+bot_word+u"');"
            print sql
            conn.execute(sql)
            self.subjectCount += 1
            text = u"@"+screen_name+u" "+screen_name+u"さん。"+self.reply_answer[self.answer_num]+u"\n現在の登録件数は"+unicode(self.subjectCount)
            self.answer_num += 1
            if self.answer_num==3:
                self.answer_num=0
            api.update_status(status = text,in_reply_to_status_id=status_id)
            self.teacher_name = ""
            self.user_word =""
        self.count+=1
        if self.count >3:
            self.teacher_name = ""
            self.user_word =""
            self.count=0

    def reaction_word(self,status):
        text = self.search_from_DB(status.text)
        if text !="":
            api.update_status(status = text)

# Twitterオブジェクトの生成
try:
    listener = Listener()
    stream = tweepy.Stream(auth, listener)
    stream.userstream()
except KeyboardInterrupt:
    print u"きた"
    conn.commit()
    conn.close()
#参考サイト
#userstreamの使いかた
# http://ha1f-blog.blogspot.jp/2015/02/tweepypythonpip-tweepymac.html
