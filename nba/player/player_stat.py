# -*- coding: utf-8 -*-
"""
Created on Fri Feb 22 14:04:38 2019

@author: song
"""

import requests
import urllib.request
from bs4 import BeautifulSoup
import re
import os
import datetime
import sys

class CustomException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

def raise_exception(err_msg):
    raise CustomException(err_msg)

def main(*args):
    global main_url
    global f_cnt
    main_url = 'https://www.basketball-reference.com'
    if len(args):
        season = args[0]
        date_from = args[1]
        date_to = args[2]
    else:
        today = datetime.datetime.now()
        if today.month > 9:
            season = today.year + 1
        elif today.month < 6:
            season = today.year
        else:
            season = ''
        date_from = datetime.datetime.strptime(today.strftime('%Y%m%d'), "%Y%m%d") - datetime.timedelta(days = 10)
        date_to = today - datetime.timedelta(days = 3)
    f_cnt = file_cnt()
    print('선수 별 url 주소를 추출 중 입니다.')
    # 시즌에 해당하지 않는 일자인 경우 파일을 생성하지 않는다.
    if season:
        f = open("player_urls_{}.txt".format(f_cnt), "a", encoding = 'utf-8')
        team_urls = team_main_link_page(main_url + '/teams/')
        urls = []
        for url in team_urls:
            team_link_page = team_roster_link_page(url, str(season))
            if team_link_page:
                player_urls = player_link_page(team_link_page, str(season))
                if player_urls:                    
                    for player_url in player_urls:
                        if player_url in urls:
                            pass
                        else:
                            urls.append(player_url)
                            f.write(player_url + '\n')
        f.close()
    else:
        pass
    print('선수 별 url 주소 추출이 완료되었습니다.')
    print('선수 페이지 스크래핑을 시작합니다.')
    # 선수 페이지 스크래핑
    file = open("player_urls_{}.txt".format(f_cnt), "r", encoding = 'utf-8')
    player_urls = file.readlines()
    total = len(player_urls)
    i = 1
    for p_url in player_urls:
        print('{}/{} url : {} 스크래핑 중 ...'.format(i, total, re.sub('\n', '', p_url)))
        scraping_check(re.sub('\n', '', p_url))  
        i += 1
    file.close()
    print('지정한 일자의 선수 데이터 추출을 시작 합니다.')
    # date_from date_to 사이 데이터만 새로 추출
    player_stat_result(date_from, date_to)
    print('작업이 완료되었습니다.')
    
def file_cnt():
    """생성된 파일을 참고하여 파일명이 중복되지 않도록 구분값을 반환"""
    c_day = datetime.datetime.now().strftime('%Y%m%d')
    file_name_compile = re.compile(r'player_stat_(\d+)_(\d+).txt')
    cnt = 1
    for file_name in os.listdir():
        date = file_name_compile.search(file_name)
        if date:
            if date.group(1) == c_day:
                if int(date.group(2)) >= cnt:
                    cnt = int(date.group(2)) + 1
            else:
                pass
        else:
            pass
    i = 5 - int(len(str(cnt)))
    return c_day + '_' + '0' * i + str(cnt)
   
def team_main_link_page(url):
    """각 팀별로 지정한 시즌의 roster 페이지 url 추출"""
    res = urllib.request.urlopen(url)
    html = res.read()
    soup = BeautifulSoup(html, 'html.parser')
    text = 'div_teams_active'
    team_table = soup.find('div', id = text)
    urls = []
    for link in team_table.findAll('a'):
        if 'href' in link.attrs:
            full_url = main_url + link.attrs['href']
            urls.append(full_url)
    return urls   

def team_roster_link_page(url, season):
    """각 팀별로 지정한 시즌의 roster 페이지 url 추출"""
    res = urllib.request.urlopen(url)
    html = res.read()
    soup = BeautifulSoup(html, 'html.parser')
    team_table = soup.find('tbody').findAll('th')
    full_url = ''
    for link in team_table:
        if re.sub('.html', '', link.find('a').attrs['href'].split('/')[3]) == season:
            full_url = main_url + link.find('a').attrs['href']
    return full_url    

def player_link_page(url, season):
    """로스터에서 각 선수별 스탯 페이지 url 추출"""
    res = urllib.request.urlopen(url)
    html = res.read()
    soup = BeautifulSoup(html, 'html.parser')
    player_urls = []
    # roster 데이터 추출
    team_roster = soup.find('table', id = 'roster')
    for text in team_roster.find('tbody').findAll('tr'):
        full_url = main_url + re.sub('.html', '/gamelog/' + season + '/', text.find('a')['href'])
        player_urls.append(full_url)
    return player_urls
    
def scraping_check(url):
    """url 주소 적합성 체크"""
    f = open("error_log_{}.txt".format(f_cnt), "a", encoding = 'utf-8')
    try:
        response = requests.get(url)
        if response.status_code == 200:
            player_stat_scraping(url)
        else:
            f.write(response.status_code+"\t"+url)
    except:
        f.write("error!!" + "\t" + url + "\n")
    finally:
        f.close()
        
def player_stat_scraping(url):
    f = open("player_temp_{}.txt".format(f_cnt), "a", encoding= 'utf-8')
#    if os.path.getsize("player_temp_{}.txt".format(f_cnt)) > 0:
#        pass
#    else:
#        f.write("f_cnt" + "\t" + "player_code" + "\t" + "season" + "\t" + "gubun" + "\t" + "no" + "\t" + "game_no" + "\t" + "date" + "\t" + "age" + "\t" + "team" + "\t" + "location" + "\t" + "opponent" + "\t" +  "result" + "\t" + "gs" + "\t" + "mp" + "\t" + "fg" + "\t" + "fga" + "\t" + "fgp" + "\t" + "3p" + "\t" + "3pa" + "\t" + "3pp" + "\t" + "ft" + "\t" + "fta" + "\t" + "ftp" + "\t" + "orb" + "\t" + "drb" + "\t" + "trb" + "\t" + "ast" + "\t" + "stl" + "\t" + "blk" + "\t" + "tov" + "\t" + "pf" + "\t" + "pts" + "\t" + "gmsc" + "\t" + "plus" + "\t" + "note" + "\n")
    res = urllib.request.urlopen(url)
    html = res.read().decode('utf-8')
    season = url.split('/')[7]
    player_code = url.split('/')[5]
    regular_table_compile = re.compile(r'<table.*?id="pgl_basic".*?<tbody>(.*?)</tbody></table>',re.DOTALL)
    regular_table = regular_table_compile.findall(html)
    playoff_table_compile = re.compile(r'<table.*?id="pgl_basic_playoffs".*?<tbody>(.*?)</tbody></table>',re.DOTALL)
    playoff_table = playoff_table_compile.findall(html)
    row_compile = re.compile(r'<tr.*?>(.*?)</tr>', re.DOTALL)
    string_compile = re.compile(r'<td.*?>(.*?)</td>', re.DOTALL)
    if regular_table:
        i = 1  
        for row in row_compile.findall(str(regular_table[0])):
            string = string_compile.findall(re.sub('<strong>|</strong>', '', re.sub('<a.*?>|</a>','',row)))
            if string:
                a = 0            
                if len(string) == 29:
    #                f.write(str(i) + '\t')
                    for text in string:
                        if a == len(string)-1:
                            f.write(text + '\t' + '' + '\n')
                        else:
                            if a == 0:
                                f.write(f_cnt + '\t' + player_code + '\t' + season + '\t'  + 'regular' + '\t' + str(i) + '\t' + text + '\t')
                            else:
                                f.write(text + '\t')
                        a += 1
                #  결장한 경우
                else:
    #                f.write(str(i) + '\t')
                    for text in string:
                        if a == len(string)-1:
                            f.write(' \t' * 22 + text + '\n')
                        else:
                            if a == 0:
                                f.write(f_cnt + '\t' + player_code + '\t' + season + '\t' + 'regular' + '\t' + str(i) + '\t' +  text + '\t')
                            else:
                                f.write(text + '\t')
                        a += 1
                i += 1
    if playoff_table:
        i = 1  
        for row in row_compile.findall(str(playoff_table[0])):
#            print(row)
            string = string_compile.findall(re.sub('<strong>|</strong>', '', re.sub('<a.*?>|</a>','',row)))
#            print(string)
            if string:
                a = 0            
                if len(string) == 29:
    #                f.write(str(i) + '\t')
                    for text in string:
                        if a == len(string)-1:
                            f.write(text + '\t' + '' + '\n')
                        else:
                            if a == 0:
                                f.write(f_cnt + '\t' + player_code + '\t' + season + '\t'  + 'playoff' + '\t' + str(i) + '\t' + text + '\t')
                            else:
                                f.write(text + '\t')
                        a += 1
                #  결장한 경우
                else:
    #                f.write(str(i) + '\t')
                    for text in string:
                        if a == len(string)-1:
                            f.write(' \t' * 22 + text + '\n')
                        else:
                            if a == 0:
                                f.write(f_cnt + '\t' + player_code + '\t' + season + '\t' + 'playoff' + '\t' + str(i) + '\t' +  text + '\t')
                            else:
                                f.write(text + '\t')
                        a += 1
                i += 1
        f.close()
        
def player_stat_result(date_from, date_to):
    # 결과파일 생성
    f = open("player_temp_{}.txt".format(f_cnt), "r", encoding= 'utf-8')
    result_file = "player_stat_{}.txt".format(f_cnt)
    f2 = open(result_file, "a", encoding= 'utf-8')
    rows = f.readlines()
    for row in rows:
        if date_from <= datetime.datetime.strptime(re.sub('-', '', row.split('\t')[6]), "%Y%m%d") <= date_to:
            f2.write(row)
        else:
            pass
    f.close()
    f2.close()
    # error_log 체크해서 error가 없을시 임시파일 삭제
    if os.path.getsize("error_log_{}.txt".format(f_cnt)) > 0:
        pass
    else:
        os.remove("error_log_{}.txt".format(f_cnt))
        os.remove("player_urls_{}.txt".format(f_cnt))
        os.remove("player_temp_{}.txt".format(f_cnt))
#    
if __name__ == "__main__":
    try:
        if len(sys.argv) == 4:
            season = sys.argv[1]
            # season 구간은 전년도 10월 1일 부터 당해년도 5월 31일까지로 지정하여 일자를 체크한다.
            season_from = datetime.datetime.strptime(str(int(season)-1) + '1001', '%Y%m%d')
            season_to = datetime.datetime.strptime(season+'0531', '%Y%m%d')
            date_from = datetime.datetime.strptime(sys.argv[2], '%Y%m%d')
            date_to = datetime.datetime.strptime(sys.argv[3], '%Y%m%d')
            if date_from > date_to:
                raise CustomException('시작일이 종료일 보다 큽니다.')
            if season_from < date_from < season_to:
                pass
            elif season_from < date_to < season_to:
                pass
            else:
                raise CustomException('{} 시즌에 해당되지 않는 일자입니다. {} ~ {} 내에서 입력가능합니다.'.format(season, str(season_from.strftime('%Y%m%d')), str(season_to.strftime('%Y%m%d'))))
            print('파일 생성을 시작합니다. 잠시만 기다려 주십시오.')          
            main(sys.argv[1], date_from, date_to)
        elif len(sys.argv) == 1:
            print('파일 생성을 시작합니다. 잠시만 기다려 주십시오.')
            main()
        else:
            raise CustomException('''
인자가 없을시 1주일 이전부터 당일까지의 데이터 추출합니다.
인자를 넣을시 시즌, 시작일, 종료일 3개의 인자가 필요합니다.
ex) player.py 2019 20181101 20190102
                                  ''')
    except CustomException as e:
        print(e)
    except ValueError:
        print('잘못된 일자입니다. 일자를 확인하세요.')