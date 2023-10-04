#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import numpy as np 
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request as ur
from urllib.request import Request, urlopen 
from copy import deepcopy
import time 
from utils_crawl import get_url, get_table_keys

RUN_FILES = ['bs_y', 'is_y', 'cf_y', 'bs_q', 'is_q', 'cf_q']
TIME_SLEEP = 2 # second

def process_one(share_code): 
    out_file_name = 'asx/{}.xlsx'.format(share_code)
    raw_file_name = 'asx/raw_{}.npy'.format(share_code)

    url_dict = get_url(share_code)

    data = dict()

    try: 
        for sheet_key in RUN_FILES:
            time.sleep(TIME_SLEEP)
            # print('---------------')
            print('Start crawling share={}, report={}'.format(share_code, sheet_key))
            url_ = url_dict[sheet_key]
            table_keys = get_table_keys(sheet_key)

            req = Request(url_, headers={'User-Agent': 'Mozilla/5.0'})    
            read_data = urlopen(req).read()
            soup_is= BeautifulSoup(read_data,'lxml')

            ls= [] # Create empty list
            for l in soup_is.find_all('div'): 
                #Find all data structure that is ‘div’
                ls.append(l.string) # add each element one by one to the list


            exclude_keys = [
                'Operating Expenses',
                'Non-recurring Events',
                table_keys['period_key'],
            ]
            ls = [e for e in ls if e not in exclude_keys] # Exclude those columns

            new_ls = list(filter(None,ls))

            def cut_invalid_in_end(dataframe): 
                assert(len(dataframe[0]) == len(dataframe[1]))
                for i in range(len(dataframe[0])):
                    if dataframe[0][i] != dataframe[1][i]:
                        break 
                invalid = range(i,len(dataframe[0]))
                new_dataframe = dataframe.drop(invalid, axis=0)
                return new_dataframe


            start_idxes = []
            for idx, e in enumerate(new_ls):
                if e == 'Item':
                    start_idxes.append(idx)

            assert(len(start_idxes) == 2 * table_keys['num_tables'])

            list_df = []
            for t_idx in range(table_keys['num_tables']): 
                if t_idx == table_keys['num_tables'] - 1:
                    short_ls = new_ls[start_idxes[t_idx*2]:]
                else:
                    short_ls = new_ls[start_idxes[t_idx*2]:start_idxes[t_idx*2+2]]
                
                is_data = list(zip(*[iter(short_ls)]*7))
                df = pd.DataFrame(is_data[0:])
                new_df = cut_invalid_in_end(df)
                # data[table_keys['tab_names'][t_idx]] = new_df
                list_df.append(new_df)

            # Concat all tables in one sheet 
            list_df = pd.concat(list_df)

            # Remove first col 
            data[sheet_key] = list_df.drop(list_df.columns[0], axis=1)

            print('Finish crawling {}'.format(sheet_key))

        with pd.ExcelWriter(out_file_name) as writer:
            for sheet_key in RUN_FILES:
                # use to_excel function and specify the sheet_name and index
                # to store the dataframe in specified sheet
                data[sheet_key].to_excel(writer, sheet_name=sheet_key, index=False)
        return True 
    except Exception as e:
        return e 

def main_process():
    # Read all codes 
    df = pd.read_csv('asx-companies-list.csv')
    codes = df['Code'] # format 'ASX:BHP'
    # codes = ['ASX:CBA', 'ASX:NAB', 'ASX:WBC', 'ASX:ANZ', 'ASX:BEN', 'ASX:BOQ'] # custom codes

    error_codes = []
    for idx, share_code in enumerate(codes): 
        # if idx < 1617: 
        #     continue
        share_code = share_code.replace('ASX:','').lower()
        print('---------------')
        print('Processing {}/{} - code = {}'.format(idx+1, len(codes), share_code))

        try:
            output = process_one(share_code)  
            if output is not True: 
                print(output)
                error_codes.append(share_code)      
        except Exception as e: 
            print(e)
            error_codes.append(share_code)


    df_error_codes = pd.DataFrame(error_codes, columns=['code'])
    df_error_codes.to_csv('error_codes.csv')
        



if __name__ == '__main__': 
    main_process()