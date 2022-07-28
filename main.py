'''
Desc: 可转债数据入口
File: /main.py
Project: convertible-bond
File Created: Saturday, 23rd July 2022 9:09:56 pm
-----
Copyright (c) 2022 Camel Lu
'''
import time
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


from utils.login import login
from utils.connect import connect
from lib.mysnowflake import IdWorker

connect_instance = connect()
connect = connect_instance.get('connect')
cursor = connect_instance.get('cursor')

# 要item字段一一对应,否则数据库插入顺序
rename_map = {
    'id': 'id',
    'cb_id': 'id',
    'cb_name': '可转债名称',
    'cb_code': '可转债代码',
    'stock_name': '股票名称',
    'stock_code': '股票代码',
    'market': '市场',

    'price': '转债价格',
    'cb_percent': '转债涨跌幅',
    'stock_price': '股价',
    'stock_percent': '股价涨跌幅',
    'arbitrage_percent': '日内套利',
    'convert_stock_price': '转股价格',
    'premium_rate': '转股溢价率',
    'cb_to_pb': ' 转股价格/PB比例',

    'remain_price': '剩余本息',
    'remain_price_tax': '税后剩余本息',

    'is_unlist': '是否上市',
    'issue_date': '发行日期',
    'date_convert_distance': '距离转股时间',
    'date_remain_distance': '距离到期时间',
    'date_return_distance': '距离回售时间',

    'remain_amount': '剩余规模',
    'market_cap': '股票市值',
    'remain_to_cap': '转债剩余/市值比例',


    'rate_expire': '到期收益率',
    'rate_return': '回售收益率',

    'old_style': '老式双底',
    'new_style': '新式双底',
    'rating': '债券评级',
}


def get_bs_source(is_read_local=False):
    # 利用BeautifulSoup解析网页源代码
    path = "output.html"
    bs = None
    if is_read_local:
        htmlfile = open(path, 'r', encoding='utf-8')
        bs = BeautifulSoup(htmlfile.read(), 'lxml')
        htmlfile.close()
    else:
        with open(path, "w", encoding='utf-8') as file:
            page_url = "https://www.ninwin.cn/index.php?m=cb&a=cb_all"
            chrome_driver = login(page_url, is_cookies_login=True)
            # 获取每页的源代码
            time.sleep(5)
            data = chrome_driver.page_source
            bs = BeautifulSoup(data, 'lxml')
            # prettify the soup object and convert it into a string
            file.write(str(bs.prettify()))
    return bs


def output_excel(df):

    df.rename(columns=rename_map, inplace=True)
    df.to_excel('cb_list.xlsx', index=False)


def store_database(df):
    sql_insert = generate_insert_sql(
        rename_map, 'convertible_bond', ['id', 'cb_id', 'cb_code'])
    list = df.values.tolist()
    cursor.executemany(sql_insert, list)
    connect.commit()


def generate_insert_sql(target_dict, table_name, ignore_list):
    keys = ','.join(target_dict.keys())
    values = ','.join(['%s'] * len(target_dict))
    update_values = ''
    for key in target_dict.keys():
        if key in ignore_list:
            continue
        update_values = update_values + '{0}=VALUES({0}),'.format(key)

    sql_insert = "INSERT INTO {table} ({keys}) VALUES ({values})  ON DUPLICATE KEY UPDATE {update_values}; ".format(
        table=table_name,
        keys=keys,
        values=values,
        update_values=update_values[0:-1]
    )
    return sql_insert


def main():

    bs = get_bs_source()
    # print(bs)
    rows = bs.find('table', id="cb_hq").find('tbody').find_all('tr')
    list = []
    worker = IdWorker()
    dt = datetime.now()
    for index in range(0, len(rows)):
        row = rows[index]
        try:
            # print(row)

            cb_id = row.get("data-id")  # 获取属性值
            cb_name = row.get("data-cb_name")
            cb_code = row.get("data-cbcode")
            stock_code = row.get("data-stock_code")[2:]
            market = row.get("data-stock_code")[0:2]
            stock_name = row.get("data-stock_name")
            price = row.get("data-cb_price")  # 可转债价格
            rating = row.get("data-rating")  # 债券评级
            cb_percent = row.find_all('td', {'class': "cb_mov2_id"})[
                0].get_text().strip()[0:-1]  # 转债涨幅
            arbitrage_percent = row.find_all('td', {'class': "cb_mov2_id"})[
                1].get_text().strip()[0:-1]  # 日内套利
            stock_price = row.find_all('td', {'class': "stock_price_id"})[
                0].string.strip()  # 股票价格
            stock_percent = row.find_all('td', {'class': "cb_mov_id"})[
                0].get_text().strip()[0:-1]  # 股票涨跌幅
            convert_stock_price = row.find_all('td', {'class': "cb_strike_id"})[
                0].get_text().strip()  # 转股价格

            premium_rate = row.find_all('td', {'class': "cb_premium_id"})[
                0].string.strip()[0:-1]  # 转股溢价率

            remain_price = row.find_all('td', {'class': "cb_price2_id"})[
                1].string.strip()  # 剩余本息
            remain_price_tax = row.find_all('td', {'class': "cb_price2_id"})[
                1]['title'].strip()[2:]  # 税后剩余本息
            is_unlist = row.get("data-unlist")  # 是否上市
            issue_date = None
            if is_unlist == 'N':
                issue_date = row.find(
                    'td', {'class': "bond_date_id"}).get_text().strip()  # 发行日期
            date_convert_distance = row.find_all('td', {'class': "cb_t_id"})[
                0].string.strip()  # 距离转股时间
            date_remain_distance = row.find_all('td', {'class': "cb_t_id"})[
                1].get_text().strip()  # 剩余到期时间 待处理异常情况
            date_return_distance = row.find_all('td', {'class': "cb_t_id"})[
                2].get_text().strip()  # 剩余回售时间 待处理异常情况

            remain_amount = row.get("data-remain_amount")  # 剩余规模
            # remain_amount = row.find_all('td', {'class': "remain_amount"})[
            #     0].get_text().strip()  # 转债剩余余额
            market_cap = row.find_all('td', {'class': "market_cap"})[
                0].get_text().strip()  # 股票市值
            remain_to_cap = row.find_all('td', {'class': "cb_to_share"})[
                0].get_text().strip()[0:-1]  # 转债剩余/市值比例

            cb_to_pb = row.find_all('td', {'class': "cb_elasticity_id"})[
                0].get_text().strip()  # 转股价格/PB比例

            rate_expire = row.find_all('td', {'class': "cb_BT_id"})[
                0].get_text().strip()[0:-1]  # 到期收益率
            rate_return = row.find_all('td', {'class': "cb_AT_id"})[
                4].get_text().strip()[0:-1]  # 回售收益率
            old_style = row.find_all('td', {'class': "cb_wa_id"})[
                0].get_text().strip()  # 老式双底
            new_style = row.find_all('td', {'class': "cb_wa_id"})[
                1].get_text().strip()  # 新式双底
            # print("market", rate_expire, rate_return,
            #       stock_name, old_style, new_style, stock_percent, date_convert_distance, date_return_distance, date_remain_distance)
            # fund_df = pd.DataFrame({'id': id_list, 'fund_code': code_list, 'morning_star_code': morning_star_code_list, 'fund_name': name_list, 'fund_cat': fund_cat,
            #                         'fund_rating_3': fund_rating_3, 'fund_rating_5': fund_rating_5, 'rate_of_return': rate_of_return})
            item = {
                'id': worker.get_id(),
                'cb_id': cb_id,
                'cb_name': cb_name,
                'cb_code': cb_code,
                'stock_name': stock_name,
                'stock_code': stock_code,
                'market': market,

                'price': price,
                'cb_percent': cb_percent,
                'stock_price': stock_price,
                'stock_percent': stock_percent,
                'arbitrage_percent': arbitrage_percent,
                'convert_stock_price': convert_stock_price,
                'premium_rate': premium_rate,
                'cb_to_pb': cb_to_pb,

                'remain_price': remain_price,
                'remain_price_tax': remain_price_tax,

                'is_unlist': is_unlist,
                'issue_date': dt.strftime('%y-%m-%d') if issue_date == '今日上市' else issue_date,
                'date_convert_distance': date_convert_distance,
                'date_remain_distance': date_remain_distance,
                'date_return_distance': date_return_distance,

                'remain_amount': remain_amount,
                'market_cap': int(market_cap.replace(",", "")),
                'remain_to_cap': remain_to_cap,


                'rate_expire': None if rate_expire == '<-100' else rate_expire,
                'rate_return': rate_return,

                'old_style': float(old_style.replace(",", "")),
                'new_style': float(new_style.replace(",", "")),
                'rating': rating,
            }
            list.append(item)
        except Exception:
            print(row)
            raise Exception

    df = pd.DataFrame.from_records(list)
    # 输出到excel
    # output_excel(df)
    # 入库
    store_database(df)
    print('success!!! data total: ', len(list))
    # time.sleep(3600)


if __name__ == "__main__":
    main()
