#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from copy import deepcopy

def get_url(share_code):
    url_bs_y = 'https://www.marketwatch.com/investing/stock/{}/financials/balance-sheet?countrycode=au'.format(share_code)
    url_bs_q = 'https://www.marketwatch.com/investing/stock/{}/financials/balance-sheet/quarter?countrycode=au'.format(share_code)

    url_is_y = 'https://www.marketwatch.com/investing/stock/{}/financials?countrycode=au'.format(share_code)
    url_is_q = 'https://www.marketwatch.com/investing/stock/{}/financials/income/quarter?countrycode=au'.format(share_code)

    url_cf_y = 'https://www.marketwatch.com/investing/stock/{}/financials/cash-flow?countrycode=au'.format(share_code)
    url_cf_q = 'https://www.marketwatch.com/investing/stock/{}/financials/cash-flow/quarter?countrycode=au'.format(share_code)

    url_dict = dict()
    url_dict['bs_y'] = url_bs_y
    url_dict['bs_q'] = url_bs_q
    url_dict['is_y'] = url_is_y
    url_dict['is_q'] = url_is_q
    url_dict['cf_y'] = url_cf_y
    url_dict['cf_q'] = url_cf_q
    return url_dict

def get_table_keys(sheet_key):
    bs_y = {
        'num_tables': 2, 
        'tab_names': ['Assets', 'Liabilities'],
        'period_key': '5-year trend',
        'important_keys': [
                'Item',
                'Cash & Short Term Investments',
                'Inventories', 
                'Total Current Assets',
                'Intangible Assets', 
                'Total Assets',
                ],
    }

    bs_q = deepcopy(bs_y)
    bs_q['period_key'] = '5- qtr trend'

    is_y = {
        'num_tables': 1, 
        'tab_names': ['Income'],
        'period_key': '5-year trend',    
        'important_keys': [],  
    }

    is_q = deepcopy(is_y)
    is_q['period_key'] = '5- qtr trend'    

    cf_y = {
        'num_tables': 3, 
        'tab_names': ['Operating Activities', 'Investing Activities', 'Financing Activities'],
        'period_key': '5-year trend',     
        'important_keys': [],     
    }    

    cf_q = deepcopy(cf_y)
    cf_q['period_key'] = '5- qtr trend'    

    if sheet_key == 'bs_y': 
        return bs_y 
    elif sheet_key == 'bs_q': 
        return bs_q
    elif sheet_key == 'is_y': 
        return is_y
    elif sheet_key == 'is_q': 
        return is_q
    elif sheet_key == 'cf_y': 
        return cf_y
    elif sheet_key == 'cf_q': 
        return cf_q