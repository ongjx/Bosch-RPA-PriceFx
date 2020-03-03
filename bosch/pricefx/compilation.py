import pandas as pd
import os
from datetime import datetime
import sys

def combinefile(file,main_df,columns):
    df = pd.read_excel(file, sheet_name='Data', dtype={'SKU': str})
    df = df[columns]
    main_df = pd.concat([main_df,df])
    return main_df

def main(curr_month=None):
    print('Running Compilation of files')
    columns = [
        "SKU",
        "Customer",
        "Deal Reason",
        "QuoteQuantity",
        "Business Unit",
        "Product Group 3",
        "Net Price",
        "Net Price Unit",
        "IPP Current",
        "IPP New",
        "FEPAA"
    ]
    path = os.getcwd()
    print('Path:', path)
    df_init = pd.DataFrame(columns=columns)

    if curr_month != None:
        files = os.listdir(os.path.join(path,'files',curr_month))       
    else:
        curr_month = str(datetime.now().month) + '_' + str(datetime.now().year)
        files = os.listdir(os.path.join(path,'files'))
        
    filename = curr_month + '_PriceFxData.xlsx'

    for i in files:
        file = os.path.join(path,'files',curr_month,i)
        df_init = combinefile(file,df_init,columns)
    
    df_init.SKU = df_init.SKU.apply('="{}"'.format)
    df_init.to_excel(os.path.join(path,'output',filename), index=False)

if __name__ == '__main__':
    main()
    