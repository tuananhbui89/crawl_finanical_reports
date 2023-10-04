#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from cgi import test
from operator import concat
from re import S
import numpy as np 
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as ur
from urllib.request import Request, urlopen 
from copy import deepcopy
import time

from scipy.fft import idct
from sqlalchemy import column 
from utils_crawl import get_table_keys, get_url

import matplotlib.pyplot as plt 

ANNUAL = ['bs_y', 'is_y', 'cf_y']
QUARTER = ['bs_q', 'is_q', 'cf_q']

INDICATORS = [
    'Item',
    # Income statement 
    'Gross Income', 
    'Gross Income Growth',
    'Gross Profit Margin', 
    'Pretax Income', 
    'Pretax Margin', 
    'Net Income', 
    'EBITDA',
    # Balance sheet 
    'Cash & Short Term Investments',
    'Inventories', 
    'Total Current Assets',
    'Intangible Assets', 
    'Total Assets',
    'Total Current Liabilities',
    'Current Ratio', 
    'Quick Ratio', 
    'Accounts Receivable Turnover',
    'Inventory Turnover',
    # Cash flow 
]

def is_number(s):
    if s == '-': 
        return True 
    s = s.replace('B','')
    s = s.replace('M','')
    s = s.replace('K','')
    s = s.replace('%','')
    s = s.replace('(','')
    s = s.replace(')','')
    if s.isnumeric():
        return True 
    else: 
        return False 

def to_numeric(s): 
    """
        Support format 
        '101' --> 101 
        '101M' --> 101000000
        '101K' --> 101000
        '-' --> NaN 
        '658.08%' --> 6.5808
        '-101M' --> -101000000
        (190.8M) --> -190800000
    """
    # number checking 
    # if not is_number(s):
    #     return s 

    if '(' in s and ')' in s: 
        s = s.replace(')', '')
        s = s.replace('(', '-')

    if 'M' in s: 
        s = s.replace('M', '')
        n = float(s) * 1000000

    elif 'K' in s: 
        s = s.replace('K', '')
        n = float(s) * 1000

    elif 'B' in s: 
        s = s.replace('B', '')
        n = float(s) * 1000000000

    elif '%' in s: 
        s = s.replace('%', '')
        n = float(s) / 100 
    
    elif s == '-':
        n = np.nan

    else: 
        n = float(s)

    return n 

def test_to_numeric():
    l = ['101', '101M', '101K', '-', '658.08%', '-101M', '(190.8M)']
    output = [to_numeric(s) for s in l]
    print(output)

def add_new_indicator(df): 

    all_fields = list(df[1])

    idict = dict()
    for i, f in enumerate(all_fields):
        idict[f] = i

    def _get_indicator(a):
        assert(a in all_fields)
        return list(df.loc[idict[a]])

    def _to_numeric(a):
        assert(a in all_fields)
        row = list(df.loc[idict[a]])
        _row = [to_numeric(s) for s in row[1:]]
        return [row[0]] + _row 

    def _ratio_a_b(a,b):
        assert(a in all_fields)
        assert(b in all_fields)
        row_a = _to_numeric(a)
        row_b = _to_numeric(b)
        row_a = row_a[1:]
        row_b = row_b[1:]
        r = [_a/_b for _a, _b in zip(row_a, row_b)]
        return r 
    
    def _current_ratio():  
        """
        "Chỉ số thanh toán hiện hành = Tài sản lưu động/ Nợ ngắn hạn"
        Chỉ số này cho biết khả năng của một công ty trong việc dùng các tài sản lưu động như tiền mặt, 
        hàng tồn kho hay các khoản phải thu để chi trả cho các khoản nợ ngắn hạn của mình. Chỉ số này càng 
        cao chứng tỏ công ty càng có nhiều khả năng sẽ hoàn trả được hết các khoản nợ. Chỉ số thanh toán 
        hiện hành nhỏ hơn 1 cho thấy công ty đang ở trong tình trạng tài chính tiêu cực, có khả năng không 
        trả được các khoản nợ khi đáo hạn. Tuy nhiên, điều này không có nghĩa là công ty sẽ phá sản bởi vì 
        có rất nhiều cách để huy động thêm vốn. Mặt khác, nếu chỉ số này quá cao cũng không phải là một 
        dấu hiệu tốt bởi vì nó cho thấy doanh nghiệp đang sử dụng tài sản chưa được hiệu quả
        """
        return ['Current Ratio'] + _ratio_a_b('Total Current Assets', 'Total Current Liabilities')

    def _quick_ratio():
        """
        Chỉ số thanh toán nhanh = (Tiền và các khoản tương đương tiền+các khoản phải thu+các khoản đầu tư ngắn hạn)/(Nợ ngắn hạn)
            Tiền và các khoản tương đương tiền + các khoản đầu tư ngắn hạn = Cash & Short Term Investments 
            các khoản phải thu = Total Accounts Receivable
            Nợ ngắn hạn = Total Current Liabilities
        """
        row_a1 = _to_numeric('Cash & Short Term Investments')
        row_a2 = _to_numeric('Total Accounts Receivable')
        row_b = _to_numeric('Total Current Liabilities')
        row_a1 = row_a1[1:]
        row_a2 = row_a2[1:]
        row_b = row_b[1:]
        r = [(_a1+_a2)/_b for _a1, _a2, _b in zip(row_a1, row_a2, row_b)]
        return ['Quick Ratio'] + r 

    def _cash_ratio():
        """
        Chỉ số thanh toán tiền mặt = (Các khoản tiền và tương đương tiền)/(Nợ ngắn hạn)
            Các khoản tiền và tương đương tiền = Cash Only
            Nợ ngắn hạn = Total Current Liabilities
        """
        return ['Cash Ratio'] + _ratio_a_b('Cash Only', 'Total Current Liabilities')

    def _short_term_debt_coverage():
        """
        Chỉ số dòng tiền hoạt động = Dòng tiền hoạt động/ Nợ ngắn hạn
            Dòng tiền hoạt động = Cash Only
            Nợ ngắn hạn = Total Current Liabilities
        """
        return ['Short-Term Debt Coverage'] + _ratio_a_b('Cash Only', 'Total Current Liabilities')
    
    def _accounts_receivable_turnover():
        return _get_indicator('Accounts Receivable Turnover')

    def _inventory_turnover():
        """
        Vòng quay hàng tồn kho = giá vốn hàng bán/ Hàng tồn kho trung bình
            giá vốn hàng bán = Cost of Goods Sold (COGS) incl. D&A
            Hàng tồn kho trung bình = Finished Goods
        Số vòng quay hàng tồn kho là số lần mà hàng hoá tồn kho bình quân luân chuyển trong kỳ. 
        Số vòng quay hàng tồn kho càng cao thì việc kinh doanh được đánh giá càng tốt, bởi lẽ doanh 
        nghiệp chỉ đầu tư cho hàng tồn kho thấp nhưng vẫn đạt được doanh số cao
        """
        return ['Inventory Turnover'] + _ratio_a_b('Cost of Goods Sold (COGS) incl. D&A', 'Finished Goods')

    # Add new row to df 
    new_indicators = [
        _current_ratio(),
        _quick_ratio(),
        _cash_ratio(),
        _short_term_debt_coverage(),
        _inventory_turnover(),
    ]

    idx = len(all_fields)
    for indicator in new_indicators:
        df.loc[idx] = indicator
        idx += 1 

    return df 

def process_one(share_code): 
    """
    Read data from excel file, add new indicators and return data
    Combine all three reports (balance sheet, income statement, cash flow) into one dataframe
    """

    out_file_name = 'asx/{}.xlsx'.format(share_code)

    data = dict()

    data['annual'] = [pd.read_excel(out_file_name, sheet_name=sheet_key) for sheet_key in ANNUAL]
    data['quarter'] = [pd.read_excel(out_file_name, sheet_name=sheet_key) for sheet_key in QUARTER]

    data['annual']  = pd.concat(data['annual'], axis=0, ignore_index=True)
    data['quarter'] = pd.concat(data['quarter'], axis=0, ignore_index=True)
    
    # Create new indicators 
    data['annual'] = add_new_indicator(data['annual'])
    data['quarter'] = add_new_indicator(data['quarter'])

    return data 

def compare_report(all_data, period='annual'): 
    """
    Read all data, remove unimportant fields, concat indicators vertically (easier to compare) and return data
    """

    codes = all_data.keys()
    
    # delete all unimportant fields 
    def _remove_unimportant_fields(df, important_fields):
        assert(type(df) is pd.DataFrame)
        new_df = deepcopy(df)
        list_idx = []
        added_fields = []
        for idx, f in enumerate(df[1]): 
            if f not in important_fields:
                list_idx.append(idx)
            if f in added_fields:
                list_idx.append(idx)
            else: 
                added_fields.append(f)
        
        new_df = new_df.drop(labels=list_idx, axis=0)
        return new_df 
    
    for share_code in codes: 
        all_data[share_code][period] = _remove_unimportant_fields(all_data[share_code][period], INDICATORS)

    # rename column header 
    for share_code in codes: 
        new_name = dict()
        for i in range(6):
            new_name[i+1] = share_code + str(i+1)
        all_data[share_code][period] = all_data[share_code][period].rename(
            columns=new_name
        )

    # concat same fields horizontal 
    # concat_df = []
    # for share_code in codes: 
    #     concat_df.append(all_data[share_code][period])
    
    # concat_df = pd.concat(concat_df, axis=1)

    # concat vertically 
    all_fields = list(all_data[share_code][period][share_code + '1'])
    all_indexes = list(all_data[share_code][period].index)
    idict = dict()
    for i, f in zip(all_indexes, all_fields):
        idict[f] = i

    concat_df = []
    for i, f in enumerate(all_fields):
        for share_code in codes: 
            # print(list(all_data[share_code][period].loc[idict[f]]))
            concat_df.append([share_code] + list(all_data[share_code][period].loc[idict[f]]))
    
    concat_df = pd.DataFrame(concat_df)

    print('------')
    print(concat_df)
    print('------')

    return concat_df

def main_process():
    # Read all codes 
    # out_file_name = 'compare/dairy.xlsx'
    # codes = ['ASX:A2M', 'ASX:BUB', 'ASX:CLV', 'ASX:AHF', 'ASX:SM1', 'ASX:NUC']

    out_file_name = 'compare/bank.xlsx'
    codes = ['ASX:CBA', 'ASX:NAB', 'ASX:WBC', 'ASX:ANZ', 'ASX:BEN', 'ASX:BOQ']

    all_data = dict()
    for idx, share_code in enumerate(codes): 
        share_code = share_code.replace('ASX:','').lower()
        print('---------------')
        print('Processing {}/{} - code = {}'.format(idx+1, len(codes), share_code))

        all_data[share_code] = process_one(share_code)  

    data = dict()
    data['annual'] = compare_report(all_data, 'annual')
    data['quarter'] = compare_report(all_data, 'quarter')

    with pd.ExcelWriter(out_file_name) as writer:
        data['annual'].to_excel(writer, sheet_name='annual', index=False)
        data['quarter'].to_excel(writer, sheet_name='quarter', index=False)


if __name__ == '__main__': 
    main_process()
    # test_to_numeric()
