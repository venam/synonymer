#!/bin/python2
"""
COPYRIGHT AND PERMISSION NOTICE

Copyright (c) 2013, Patrick Louis <patrick at unixhub.net>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    1.  The author is informed of the use of his/her code. The author does not have to consent to the use; however he/she must be informed.
    2.  If the author wishes to know when his/her code is being used, it the duty of the author to provide a current email address at the top of his/her code, above or included in the copyright statement.
    3.  The author can opt out of being contacted, by not providing a form of contact in the copyright statement.
    4.  If any portion of the author's code is used, credit must be given.
            a. For example, if the author's code is being modified and/or redistributed in the form of a closed-source binary program, then the end user must still be made somehow aware that the author's work has contributed to that program.
            b. If the code is being modified and/or redistributed in the form of code to be compiled, then the author's name in the copyright statement is sufficient.
    5.  The following copyright statement must be included at the beginning of the code, regardless of binary form or source code form.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Except as contained in this notice, the name of a copyright holder shall not
be used in advertising or otherwise to promote the sale, use or other dealings
in this Software without prior written authorization of the copyright holder.

synonymer.py

CREATE TABLE words (word VARCHAR PRIMARY KEY, synonym VARCHAR, antonym VARCHAR);
"""
import random
import sys
import sqlite3
import json
import re
from urllib import URLopener

import printer

class words_class:
	def __init__(self,word,black):
		self.black    = black
		self.word     = word
		self.new_word = word

class synonymer:
	"""
	constructor
	"""
	def __init__(self,text_file,config_file):
		try:
			self.text_file          = open(text_file).read()
		except Exception,e:
			print printer.FAIL+ str(e)
			print printer.MINUS+"Problem opening the file"
			exit(1)
		self.config             = self.read_conf(config_file)
		self.br                 = URLopener()
		self.counter            = 1
		self.jump               = 0
		self.words              = []
		self.punctuation        = []
		self.starts_with_punc   = False
		self.total_words        = 0
		self.total_black        = 0
		self.array_of_non_black = []
		self.dist               = []
		self.weights = {
			's': 1,
			'a': 1,
		}
		self.black_list         =  []
		self.create_black_list(self.config['black_list'])
		#connect to the db
		try:
			self.conn      = sqlite3.connect(self.config['database'])
			self.cur       = self.conn.cursor()
		except Exception,e:
			print printer.FAIL+ str(e)
			print printer.MINUS+ "Problem connecting to the database"
			exit(1)

	"""
	prepare the configs
	"""
	def read_conf(self,config_file):
		try:
			return json.load(open(config_file))
		except Exception,e:
			print printer.FAIL+str(e)
			print printer.MINUS+"Cannot load the specified config file"
			exit(1)

	"""
	split the file and fill the words array, augment the 
	total word count, black word count, and fill the  array 
	with the index of the words that are going to be changed
	"""
	def split(self):
		spl = re.findall("[\w]+",self.text_file)
		if not re.findall("(^\w)",self.text_file):
			#meaning we have to loop through the punctuation array then the words array
			self.starts_with_punc = True
		self.punctuation = re.findall(r"[^\w]+", self.text_file)
		for word in spl:
			self.array_of_non_black.append(self.total_words)
			self.total_words +=1
			word_classed = words_class(word,False)
			if self.in_black_list(word):
				self.total_black +=1
				word_classed.black = True
			self.words.append(word_classed)

	def create_black_list(self,black_list_file):
		try:
			f = open(black_list_file,'r').readlines()
			for w in f:
				w  = w.rstrip()
				self.black_list.append(w)
		except Exception,e:
			print printer.FAIL+str(e)
			print printer.MINUS+"Problem creating the blacklist"
			exit(1)

	def in_black_list(self,word):
		if word.lower() in self.black_list:
			return True
		return False

	def adjust_frequency(self):
		a_w = self.config['synonym_freq']
		if a_w<1 and a_w>0.01:
			b_w = float(1-a_w)
			self.weights['s'] = int( a_w *100)
			self.weights['a'] = int(b_w *100)
			for x in self.weights.keys():
				self.dist += self.weights[x] * x
		else:
			print printer.MINUS+"Problem, frequency not between the bound"
			exit(1)
		#multiply the frequency by the nb of words left. == the step_nb
		self.jump = (1-self.config['word_freq']) * len(self.array_of_non_black)

	def search_synonyms_online(self,word):
		word        = word.replace(" ","%20")
		try:
			response    = self.br.open("http://m.dictionary.com/synonym/"+word).readlines()
		except Exception,e:
			print printer.FAIL+str(e)
			print printer.MINUS+"Problem fetching the synonym online"
			return -1
		for a in response:
			if "No results found for" in a:
				return []
			if "Definition" in a:
				a = a.split("Synonyms:</b> ")
				a = a[1]
				a = a.replace("</div>","")
				a = a.replace("\r","")
				a = a.replace("\n","")
				a = a.split(", ")
				break
		synonyms    = a
		return synonyms

	def search_antonyms_online(self,word):
		word        = word.replace(" ","%20")
		try:
			response    = self.br.open("http://m.dictionary.com/antonym/"+word).readlines()
		except Exception,e:
			print printer.FAIL+str(e)
			print printer.MINUS+"Problem fetching the antonym online"
			return -1
		for a in response:
			if "No results found for" in a:
				return []
			if ">Antonyms:</b>" in a:
				a = a.split(">Antonyms:</b> ")[1]
				a = a.replace("</div>","")
				a = a.replace("\r","")
				a = a.replace("\n","")
				a = a.split(", ")
				break
		antonyms   = a
		return antonyms

	def search_db(self,word):
		self.cur.execute("SELECT * FROM words WHERE word='"+word+"';")
		ls = list(self.cur)
		if len(ls) <1:
			print printer.INFO+"Word not found in the db"
			return False
		else :
			return ls

	"""
	commit changes to the db
	"""
	def commit(self):
		self.conn.commit()

	def add_to_the_db(self,word,synonyms,antonyms):
		st_syn = ";".join(synonyms)
		st_ant = ";".join(antonyms)
		query = 'INSERT INTO words VALUES("'+word+'","'+st_syn+'","'+st_ant+'");'
		self.cur.execute(query);
		self.commit()

	def add_to_black_list(self,word):
		self.black_list.append(word)

	def save_black_list(self):
		open(self.config['black_list']+".bak",'w').write( open(self.config['black_list'],'r').read() )
		open(self.config['black_list'],'w').write("")
		for a in self.black_list:
			open(self.config['black_list'],'a').write(a+"\n")

	def syn_or_ant(self):
		results = {}
		wRndChoice = random.choice(self.dist)
		results[wRndChoice] = results.get(wRndChoice, 0) + 1
		if results.get('s'):
			return True
		else:
			return False

	def change(self,word_to_change):
		#choose betweeen syn and ant here
		syn = self.syn_or_ant()
		#search db for word
		db_data = self.search_db(word_to_change.word)
		#if it's found
		if db_data != False:
			db_data = db_data[0]
			word_syn = db_data[1].split(";")
			word_ant = db_data[2].split(";")
			if word_syn[0] == "" and word_ant[0] == "":
				print printer.INFO+"A word was saved in the DB and it didn't have any syn nor ant!"
				self.add_to_black_list(word_to_change.word)
				return False
			if syn:
				#search db for syn
				#no syn in the db use the ant instead
				if word_syn[0] == "":
					word_to_change.new_word = "not "+random.choice(word_ant)
				else:
					word_to_change.new_word = random.choice(word_syn)
			else:
				#search db for ant
				#no ant in the db use the syn instead
				if word_ant[0] == "":
					word_to_change.new_word = random.choice(word_syn)
				else:
					word_to_change.new_word = "not "+random.choice(word_ant)
		#if notthing in the db, fetch online
		else:
			print printer.INFO+ "Fetching online"

			print printer.INFO+"Fetching synonym"
			word_syn = self.search_synonyms_online(word_to_change.word) 
			if word_syn != -1:
				if len(word_syn) != 0:
					print printer.PLUS+ "Synonym found"
				else:
					print printer.WARN+ "Synonym not found"

			print printer.INFO+"fetching antonym"
			word_ant = self.search_antonyms_online(word_to_change.word)
			if word_ant != -1:
				if len(word_ant) != 0:
					print printer.PLUS+ "Antonym found"
				else:
					print printer.WARN+ "Antonym not found"

			if word_ant == -1 or word_syn == -1:
				return False

			if len(word_syn) ==0  and len(word_ant)==0:
				#add to blacklist
				print printer.MINUS+"Word added to the blacklist"
				self.add_to_black_list(word_to_change.word)
				return False

			if syn:
				#no syn, change to ant instead
				if len(word_syn) ==0:
					word_to_change.new_word = "not "+random.choice(word_ant)
				else:
					word_to_change.new_word = random.choice(word_syn)
			else:
				if len(word_ant) ==0:
					word_to_change.new_word = random.choice(word_syn)
				else:
					word_to_change.new_word = "not "+random.choice(word_ant)
			#update the db with the 2 of them
			self.add_to_the_db(word_to_change.word,word_syn, word_ant)
		return True

	def update_words(self):
		for a in self.words:
			self.counter +=1
			if self.counter > self.jump-1 and a.black == False:
				stat = self.change(a)
				if stat :
					# if the word was changed without problem continue to count
					self.counter  = 1
				else:
					#if there was a problem change the next word instead
					self.counter = self.jump-1
		self.save_black_list()

	def display(self):
		i             = 0
		string_output = ""
		if self.starts_with_punc:
			for a in self.words:
				string_output+= self.punctuation[i]
				string_output+= a.new_word
				i+=1
			string_output+=self.punctuation[i]
		else:
			for a in self.words:
				string_output+=a.new_word
				string_output+=self.punctuation[i]
				i+=1
		print string_output

	def procedure(self):
		self.split()
		self.adjust_frequency()
		self.update_words()
		self.display()
