# -*- coding:utf-8 -*-
import tkinter as tk  # 使用Tkinter前需要先导入
import tkinter.messagebox
import pickle
from bs4 import BeautifulSoup
from selenium import webdriver
#from selenium.webdriver.support.wait import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.common.by import By
import  requests
#import  request
import  time
import  re
import sys
#import  copy
import argparse
import xlsxwriter
import pandas as pd
import numpy as np

# 第1步，实例化object，建立窗口window
window = tk.Tk()

# 第2步，给窗口的可视化起名字
window.title('东方财富网数据统计')

# 第3步，设定窗口的大小(长 * 宽)
window.geometry('800x600')  # 这里的乘是小x

# 第4步，加载 wellcome image
canvas = tk.Canvas(window, width=800, height=135, bg='green')
image_file = tk.PhotoImage(file='pic.gif')
image = canvas.create_image(200, 0, anchor='n', image=image_file)
canvas.pack(side='top')
tk.Label(window, text='数据统计', font=('Arial', 16)).pack()

# 第5步，用户信息
tk.Label(window, text='统计起始日期:', font=('Arial', 14)).place(x=10, y=170)
tk.Label(window, text='统计结束日期:', font=('Arial', 14)).place(x=10, y=210)

# 第6步，用户登录输入框entry
# 统计起始日期
var_begin_date = tk.StringVar()
var_begin_date.set('2020-01-01')
entry_begin_date = tk.Entry(window, textvariable=var_begin_date, font=('Arial', 14))
entry_begin_date.place(x=170, y=175)
# 统计结束日期
var_end_date = tk.StringVar()
entry_end_date = tk.Entry(window, textvariable=var_end_date, font=('Arial', 14))
entry_end_date.place(x=170, y=215)

tk.Label(window, text='说明：', font=('Arial', 12)).place(x=10, y=300)
tk.Label(window, text='1.使用前需在此文件目录下新建kjtj.xls，确保文件内容为空。', font=('Arial', 12)).place(x=10, y=330)
tk.Label(window, text='2.统计为输入时间范围内的新股数据，不包括科创板股票', font=('Arial', 12)).place(x=10, y=360)
tk.Label(window, text='3.统计为连续未开板时买入上榜营业部信息，以涨幅大于9.9%计算。', font=('Arial', 12)).place(x=10, y=360)
tk.Label(window, text='作者：mash', font=('Arial', 12)).place(x=650, y=550)
#btn_sign_up = tk.Button(window, text='Sign up', command=usr_sign_up)
#btn_sign_up.place(x=200, y=240)


"""
本脚本用于爬取财富网龙虎榜数据
1，点击首页新股
2，选择所有开头非688 且在指定日期内的股票
3，进入数据页面，选择明细
4，进入明细页面，选择买入前五的营业部数据
"""
"""
坑1：表格是异步加载的，所以需要selenium做模拟器浏览
坑2: driver 最好一个作用域一个，这样防止混乱
"""
baseurl = "http://www.eastmoney.com"
data_url = 'http://data.eastmoney.com'
driver_path = 'D:\SeleniumPython\Test_framework\drivers\chromedriver.exe'
#//*[@id="main-table_paginate"]/a[2]

"""获得明细链接的龙虎榜数据"""
def get_deatail_data(href):
    ret_list = []
    href = data_url + href
    driver = webdriver.Chrome(driver_path)
    driver.get(href)
    time.sleep(5)
    driver.get(href)
    datail_content = driver.execute_script("return document.documentElement.outerHTML")
    # tab-2 > tbody
    datail_soup = BeautifulSoup(datail_content,'lxml')
    tr_list_soup = datail_soup.select('#tab-2 > tbody')
    data_date= str(datail_soup.select('div.content:nth-child(7) > div:nth-child(1) > div:nth-child(1)'))
    #print(data_date)
    if len(tr_list_soup) <= 0 :
        return ret_list
    a_date = data_date[data_date.index(var_begin_date.get()[0:4]):]
    #print(a_date)
    d_date = a_date[0:10]
    #print(d_date)
    #print(tr_list_soup,'-----')
    index = 1
    for tr in tr_list_soup[0]:
        str_selector = '#tab-2 > tbody > tr:nth-child({}) > td:nth-child(2) > div.sc-name > a:nth-child(2)'.format(index)
        part_soup = datail_soup.select(str_selector)

        if len(part_soup)<=0:
            continue
        if(index == 1):
            ret_list.append(d_date)
        ret_list.append(part_soup[0].string)
        index = index + 1
    driver.quit()
    return ret_list

#tab-2 > tbody > tr:nth-child(1) > td:nth-child(2) > div.sc-name > a:nth-child(2)
#tab-2 > tbody > tr:nth-child(2) > td:nth-child(2) > div.sc-name > a:nth-child(2)
# tab-2 > tbody > tr:nth-child(3) > td:nth-child(2) > div.sc-name > a:nth-child(2)

"""获得新股连接的url地址"""
def get_new_share_url():
    # 得到东方财富网首页数据
    main_page_ret = requests.get(baseurl)
    main_page_soup = BeautifulSoup(main_page_ret.text, 'lxml')
    # print(main_page_ret.text)
    # 右键点击新股票，在右键 copy->selector,得到如下字符串
    new_share_path = 'body > div.main.search-module > div.hq-nav > div > div.hq-con > div.hq-con-data.hqzx-data > div.menu-data.hqzx-menu > a:nth-child(9)'
    new_share_content = main_page_soup.select(new_share_path)
    assert len(new_share_content) == 1
    return new_share_content[0].get('href')

    # for tr in new_share_content[0].find_all('tr'):
    #     href = t.find('a').get('href')

"""通过营业部数据链接获取买入前五名的营业部名字"""
def get_buisness_more_list(stock_data_url):
    driver = webdriver.Chrome(driver_path)
    driver.get(stock_data_url)
    time.sleep(3)
    buisness_part_html = driver.execute_script("return document.documentElement.outerHTML")
    buisness_part_soup = BeautifulSoup(buisness_part_html,'lxml')
    more_selector = '#m_lhbd > div:nth-child(1) > div:nth-child(3) > a:nth-child(1)'
    new_more_content = buisness_part_soup.select(more_selector)
    assert len(new_more_content) == 1
    more_list_url = new_more_content[0].get('href')

    data_part_list = get_buisness_part_list(data_url+more_list_url)
    driver.quit()
    return data_part_list

"""通过营业部数据链接获取买入前五名的营业部名字"""
def get_buisness_part_list(stock_data_url):
    driver = webdriver.Chrome(driver_path)
    driver.get(stock_data_url)
    time.sleep(3)
    buisness_part_html = driver.execute_script("return document.documentElement.outerHTML")
    buisness_part_soup = BeautifulSoup(buisness_part_html,'lxml')
    tr_body_soup = buisness_part_soup.select('#tab-2 > tbody')

    # m_lhbd > div > table > tbody > tr:nth-child(1)
    assert len(tr_body_soup) > 0
    tr_body_soup = tr_body_soup[0]

    #print(data_date ,chg)
    ret_list = []
    row = 0
    a_list = tr_body_soup.find_all('a')
    data_list = list()
    for elem in a_list:
        if(elem.string == '明细'):
            row = row + 1
    for i in range(0,row):
        data_date_soup,data_date = get_chg_soup(buisness_part_soup , i+1 , 2)
        data_date_soup ,chg = get_chg_soup(buisness_part_soup , i+1 , 5)
        print(data_date , chg)
        data_list.append([data_date,chg])
    data_list.sort()
    print(data_list)
    kb_date = '2000-01-01'
    for j in range(0,row):
        if (float((data_list[j][1])[:(data_list[j][1]).index('%')]) > 9.90):
            kb_date = data_list[j][0]
        else:
            break
    for elem in a_list:
        if(elem.string != '明细'):
            continue
        str_href1 = str(elem.get('href'))
        str_href2 = str_href1[str_href1.index(var_begin_date.get()[0:4]):]
        str_href = str_href2[0:10]
        print(kb_date)
        if(str_href > kb_date):
            continue
        part_lsit = get_deatail_data(elem.get('href'))
        ret_list.append(part_lsit)
    driver.quit()
    return ret_list

"""获得数据行的url"""
def get_data_url_soup(stock_list_soup, row_index):
    str_code_str = '#table_wrapper-table > tbody > tr:nth-child({}) > td.listview-col-Links > a:nth-child(3)'.format(row_index)
    soup = stock_list_soup.select(str_code_str)
    """获得股票名称，代码，上市日期的soup"""
    return soup

def get_table_soup(stock_list_soup, row_index,sub_index):
    str_info = '#table_wrapper-table > tbody > tr:nth-child({}) > td:nth-child({})'.format(row_index, sub_index)
    soup = stock_list_soup.select(str_info)
    if len(soup) <= 0:
        print("Error:get staock info failed!!!")
        sys.exit(1)
    return soup,soup[0].string

"""获得数据日期和涨跌幅"""
def get_chg_soup(stock_list_soup, date_index,chg_index):
    str_info = '#tab-2 > tbody:nth-child(2) > tr:nth-child({}) > td:nth-child({}) > span:nth-child(1)'.format(date_index, chg_index)
    soup = stock_list_soup.select(str_info)
    if len(soup) <= 0:
        print("Error:get staock info failed!!!")
        sys.exit(1)
    return soup,soup[0].string

"""获取参数"""
def get_parse():
    parser = argparse.ArgumentParser(description="Spider Demo")
    parser.add_argument('-n', '--year', default=2019)
    parser.add_argument('-s', '--month', default=10)
    parser.add_argument('-p', '--prefix', default='688')
    args = parser.parse_args()
    return args.year,args.month,args.prefix

def tj_begin():
    year,month,prefix = get_parse()
    new_share_url = get_new_share_url()
    print(new_share_url)
    driver = webdriver.Chrome(driver_path)
    driver.get(new_share_url)
    time.sleep(3)
    stock_list_html =  driver.execute_script("return document.documentElement.outerHTML")
    #print(stock_list_html)
    stock_list_soup = BeautifulSoup(stock_list_html,'lxml')
    #每一列的索引下标
    row_index = 1
    code_index = 2
    stock_name_index = 3
    data_url_index = 4
    listed_date_index = 18

    # table_wrapper-table > tbody > tr:nth-child(1) > td:nth-child(18)
    # table_wrapper-table > tbody > tr:nth-child(2) > td:nth-child(18)
    #input_data = '{}-{}-01'.format(year,month)
    input_data = var_begin_date.get()
    if month+1 > 12:
        year = year+1
        month = month + 1
    #input_data_end = '{}-{}-01'.format(year,month+1)
    input_data_end = var_end_date.get()
    re_prefix = '^' + prefix +'\d{3}$'
    stock_pattern = re.compile(re_prefix)
    print(input_data,input_data_end)
    final_info = []

    while 1:
        if(row_index > 20):
            row_index = 1
            elem = driver.find_elements_by_xpath("//*[@id=\"main-table_paginate\"]/a[2]")
            print(elem)
            elem[0].click()
            time.sleep(2)
            driver.get(new_share_url)
            time.sleep(2)
            stock_list_html = driver.execute_script("return document.documentElement.outerHTML")
            # print(stock_list_html)
            stock_list_soup = BeautifulSoup(stock_list_html, 'lxml')
        """筛掉所有小于给定日期的股票"""
        listed_date_soup,str_stock_date = get_table_soup(stock_list_soup,row_index,listed_date_index)
        listed_date = listed_date_soup[0].string
        print(row_index,listed_date)
        if listed_date >= input_data_end:
            row_index = row_index + 1
            continue
        if listed_date < input_data:
            break
        code_soup,str_stock_code = get_table_soup(stock_list_soup, row_index, code_index)
        stack_code = code_soup[0].a.string
        """筛掉所有以688开头的6位数股票"""
        if  stock_pattern.search(stack_code):
            row_index = row_index + 1
            continue
        stock_name_soup,str_stock_name = get_table_soup(stock_list_soup, row_index, stock_name_index)
        stock_name = stock_name_soup[0].a.string
        data_url_soup = get_data_url_soup(stock_list_soup,row_index)
        # table_wrapper-table > tbody > tr:nth-child(15) > td.listview-col-Links > a:nth-child(3)
        stock_data_url  = data_url_soup[0].get('href')
        part_list = get_buisness_more_list(stock_data_url)
        #part_list = get_buisness_part_list(data_url+more_list_url)
        final_dic = {'股票代码':str_stock_code,'股票名称':str_stock_name,'上市日期':str_stock_date,'营业部信息':part_list}
        final_info.append(final_dic)
        row_index = row_index + 1
        pf1 = pd.read_excel('kjtj.xls')
        pf2 = pd.DataFrame.from_dict(final_dic)
        pf3 = pf1.append(pf2,ignore_index=True,sort=False)
    #order = ['股票代码' , '股票名称' , '上市日期' , '营业部信息' ]
    #pf = pf[order]
        pf3.to_excel('kjtj.xls' , encoding='utf-8' , index=False)

    #将营业部一列拆分成多列
    df = pd.read_excel('kjtj.xls')
    df2 = df['营业部信息'].str.split(',',expand=True)
    df2.head()
    df3 =df.drop('营业部信息',axis=1).join(df2)
    df3.head()
    df3.to_excel('kjtj.xls')

    print(final_info)
    driver.quit()

# 第7步，login and sign up 按钮
btn_login = tk.Button(window, text='开始统计', command=tj_begin)
btn_login.place(x=120, y=250)

# 第10步，主窗口循环显示
window.mainloop()

