# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 13:54:45 2019

@author: song
"""

import pymssql
import os
#import apscheduler
#from apscheduler.schedulers.background import BackgroudScheduler
#from apscheduler.jobstores.base import JobLookupError
import time
import re
import json

class CustomException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

def raise_exception(err_msg):
    raise CustomException(err_msg)
    
def main():
    player_stat_bcp()
    
def config_read():
    f = open("config.json", "r", encoding = 'utf-8')
    config = json.loads(f.read().encode('utf-8'))
    f.close()
    return config

def connect():
    try:
        DATABASE_CONFIG_DIC = config_read()['DATABASE_CONNECTION_INFO'][0]
        if DATABASE_CONFIG_DIC['DBMS'] == 'MSSQL':
            H = DATABASE_CONFIG_DIC['IP'] + ':' + DATABASE_CONFIG_DIC['PORT']
            U = DATABASE_CONFIG_DIC['USER']
            P = DATABASE_CONFIG_DIC['PASS']
            D = DATABASE_CONFIG_DIC['DATABASE']
            conn = pymssql.connect(host=H, user = U, password = P, database = D, login_timeout = 1)
        return conn
    except KeyError as e:
        print("KeyError: config 파일에 {}가 없습니다.".format(e))
    except pymssql.OperationalError as e:
        print(e)

def player_stat_bcp():
    try:
        DATABASE_CONFIG_DIC = config_read()['DATABASE_CONNECTION_INFO'][0]
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(
                '''
                SELECT FILE_NAME, YN FROM CRAWLER_CHECK_SBS WHERE GUBUN = 'PS'
                ''')
        rows = cursor.fetchall()
        player_stat_path = os.path.join(os.getcwd(), 'player')
        player_stat_file_list = os.listdir(player_stat_path)
        crawler_check_dic = {}
        for row in rows:
            crawler_check_dic[row[0]] = row[1]
        for player_stat_file_name in player_stat_file_list:
            if player_stat_file_name[0:11] == 'player_stat' and len(player_stat_file_name) == 30:                
                if crawler_check_dic.get(player_stat_file_name):
                    pass
                else:
                    # temp 테이블로 데이터 BCP
                    cmd_statement = 'BCP DBO.PLAYER_STAT_SBS_TEMP IN {} -c -S{} -U{} -P{}'.format(os.path.join(os.getcwd(), 'player', player_stat_file_name), DATABASE_CONFIG_DIC['IP'] + ',' + DATABASE_CONFIG_DIC['PORT'], DATABASE_CONFIG_DIC['USER'], DATABASE_CONFIG_DIC['PASS'])
                    os.system(cmd_statement)
                    insert_query = "INSERT INTO CRAWLER_CHECK_SBS VALUES ('{}', 'PS', 'Y')".format(player_stat_file_name)
                    f_no_compile = re.compile(r'player_stat_(\w+).txt')
                    f_no = f_no_compile.search(player_stat_file_name)
                    cursor.execute("EXEC DBO.UP_NBA_TABLE_APPLY @P_CD_LINK = '101', @P_F_NO = '{}'".format(f_no.group(1)))
                    cursor.execute(insert_query)
                    conn.commit()
            else:
                pass        
        conn.close()
    except:
        print('오류')

if __name__ == "__main__":
    main()