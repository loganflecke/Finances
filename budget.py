# %%
import pandas as pd
import datetime
import os
import re
import json
from dataclasses import dataclass
import merchant_intelligence
from dateutil.relativedelta import relativedelta

import importlib
importlib.reload(merchant_intelligence)

# %%
date_format = "%Y-%m-%d"
local_merch_intel_filename = "local_merch_intel.csv"
local_category_mapping_filename = "local_category_mapping.json"
transaction_path = "./Transactions"
banking_path = "./Banking"
cap_one_path = "./COC"
hysa_path = "./HYSA"
excel_filename = "budget.xlsx"
merchant_intelligence_filename = "merchant_intelligence.csv"
excel = True
merch_intel = True

# This just has to be a substring of the paths defined above that should be categorized as their account name
investment_accounts = ["COC", "HYSA"]
account_names = [transaction_path, banking_path, cap_one_path, hysa_path]
account_names = (re.search(r'[^\\/]+(?=[\\/]?$)', account).group(0) for account in account_names)

# %%
# Number of months to collect, parse, and analyze financial data
lookback_months = 8

###### CSV Header Names ######
## Global Columns, or one that should be normalized to be global, such as date and cost
category = 'Category'
description = 'Description'
date = 'Date'
cost = 'Amount'

## Credit Card CSV Columns
transaction_date = 'Transaction Date'
transaction_cost = 'Debit'

## Bank Account CSV Columns
banking_date = "Date"
banking_cost = "Amount"

## Capital One 360 Account CSV Columns
co_360_date = 'Transaction Date'
co_360_retailer = 'Transaction Description'
co_360_cost = 'Transaction Amount'
co_360_balance = 'Balance'

## THESE ARE THE NAMES OF GROCERIES AS THEY APPEAR ON THE TRANSACTIONS CSV FILE
grocery_keywords = ['KROGER', 'GIANT', 'SAFEWAY', 'HELLOFRESH', 'WEGMANS', 'FOOD LION']

###### Mappings and Lookups ######
with open(local_category_mapping_filename, 'r') as file:
    local_category_mapping = json.load(file)

transaction_to_expenses_lookup = {
    "Gas/Automotive" : "Gas",
    "Health Care" : "Healthcare",
    "Entertainment" : "Other"
}

# %%
@dataclass
class MonthlyModel:
    month: str
    net: str
    income: float
    expenses: float
    fixed_expenses: float
    variable_expenses: float
    discretionary_expenses: float
    investments: float
    hy_savings: float

# %%
def sort_df_by_date(df, date_field):
    df[date_field] = pd.to_datetime(df[date_field], format='mixed')
    df = df.sort_values(by=date_field, ascending=True)
    df = df.reset_index(drop=True)
    df[date_field] = df[date_field].dt.strftime('%Y-%m-%d')
    return df

# %%
def merge_events(input_file_path, negate_cost):
    # Ingest CSV lines
    input_events = [os.path.join(input_file_path, f) for f in os.listdir(input_file_path) if os.path.isfile(os.path.join(input_file_path, f))]
    input_df = [pd.read_csv(file) for file in input_events]
    merged_events = pd.concat(input_df)
    # Normalize column names
    column_field_mapping = {
        cost : [banking_cost, transaction_cost, co_360_cost],
        description : [co_360_retailer],
        date : [banking_date, transaction_date, co_360_date]
    }
    for col in column_field_mapping:
        for field in column_field_mapping[col]:
            if field in merged_events.columns:
                merged_events = merged_events.rename(columns={field: col})
                break
    # Dedup
    merged_events = merged_events.drop_duplicates(subset=[cost, description, date])
    # Remove $0 events
    merged_events = merged_events[merged_events[cost].notna()]
    
    # Fill in categories
    if not category in merged_events.columns:
        # Fill in category for investment accounts
        if (investment_account in input_file_path for investment_account in investment_accounts):
            merged_events[category] = str(input_file_path).replace("./", "")
        # Populate the 'category' column based on description
        for category_value, descriptions in local_category_mapping.items():
            merged_events.loc[merged_events[description].str.contains("|".join(descriptions)), category] = category_value
        # Fill in "Other" for events not defined in the lookup
        merged_events.loc[merged_events[category].isna(), category] = "Other"
        merged_events = sort_df_by_date(merged_events, date)
    if negate_cost:
        merged_events = merged_events.assign(**{cost: -merged_events[cost]})
    return merged_events

# %%
def filter_events_by_date(start_date, end_date, merged_events):
    filtered_events = merged_events[(pd.to_datetime(merged_events[date], format=date_format) >= start_date) & 
                        (pd.to_datetime(merged_events[date], format=date_format) <= end_date)].sort_values(by=date, ascending=True) 
    return filtered_events

# %%
def enrich_grocery(merged_transactions):
    for keyword in grocery_keywords:
        contains_keyword = merged_transactions[description].str.contains(keyword, case=False, na=False)
        not_fuel = ~merged_transactions[description].str.contains('FUEL', case=False, na=False)
        if contains_keyword.any() and not_fuel.any():
            merged_transactions.loc[contains_keyword & not_fuel, category] = 'Grocery'
    return merged_transactions

# %%
# Returns normalized event df of all events
# Input a dict of dfs (key: df name; value: df; negate_cost_for={df name} for dfs where expenses are positive) 
def merge_cash_flow(dfs):
    frames = []
    for name, df in dfs.items():
        frames.append(df[[date, description, category, cost]])

    return pd.concat(frames, ignore_index=True).sort_values(by=date)

# %%
# Return income and expense dfs
# Input a df of merged events
def get_cash_flow(event_dfs: pd.DataFrame):
    exception_categories = ["HYSA Transfer", "Investments", "Credit Card"]
    event_dfs = event_dfs[~event_dfs[category].isin(exception_categories)]
    income_df, expenses_df = pd.DataFrame(), pd.DataFrame()
    income_df = event_dfs[event_dfs[cost] > 0]
    expenses_df = event_dfs[event_dfs[cost] < 0]
    expenses_df.loc[:, cost] = expenses_df.loc[:, cost].abs()
    return income_df, expenses_df

# %%
# Return fixed, variable, and discretionary expenses from an expenses df
# Input expenses df
def define_expenses(expenses_df):
    # Rent, insurance, internet
    fixed_expenses_df = expenses_df[expenses_df[category].isin(["Rent", "Car Insurance", "Health Care", "Internet"])]
    # Groceries, gas, vet
    variable_expenses_df = expenses_df[expenses_df[category].isin(["Gas/Automotive", "Grocery", "Professional Services"])]
    # Dining, coffee, entertainment
    discretionary_expenses_df = expenses_df[
        ~expenses_df[category].isin(fixed_expenses_df[category].unique())
        & ~expenses_df[category].isin(variable_expenses_df[category].unique())]
    return fixed_expenses_df, variable_expenses_df, discretionary_expenses_df

# %%
# Return the MonthlyModel dataclass
def build_cashflow_model(month_start, master_events_df, income_df, expenses_df):
    fixed_expenses_df, variable_expenses_df, discretionary_expenses_df = define_expenses(expenses_df)
    return MonthlyModel(
        month = month_start,
        net = income_df[cost].sum() - expenses_df[cost].sum(),
        income = income_df[cost].sum(),
        expenses = expenses_df[cost].sum(),
        fixed_expenses = fixed_expenses_df[cost].sum(),
        variable_expenses = variable_expenses_df[cost].sum(),
        discretionary_expenses = discretionary_expenses_df[cost].sum(),
        investments = abs(master_events_df.loc[master_events_df[category] == "Investments", cost].sum()),
        hy_savings = master_events_df.loc[master_events_df[category] == "HYSA", cost].sum()
    )

# %%
# Perform the data processing and analysis for a dict event dfs (key: df name; value: df)
# Returns the monthly model
# Input a dict of dfs (key: df name; value: df)
def get_state(merged_event_dfs, month_start, month_end):
    # Get time period (length of unit of time minus 1 day)
    filtered_transactions = filter_events_by_date(month_start, month_end, merged_event_dfs["transactions"])
    filtered_banking = filter_events_by_date(month_start, month_end, merged_event_dfs["banking"])
    filtered_coc = filter_events_by_date(month_start, month_end, merged_event_dfs["coc"])
    filtered_hysa = filter_events_by_date(month_start, month_end, merged_event_dfs["hysa"])

    master_events_df = merge_cash_flow(
        {
            "transactions": filtered_transactions,
            "banking": filtered_banking,
            "coc": filtered_coc,
            "hysa": filtered_hysa,
        }
    )
    income_df, expenses_df = get_cash_flow(master_events_df)
    return build_cashflow_model(month_start, master_events_df, income_df, expenses_df)

# %%
# Returns a df of X number of monthly models, one per row
# Input a dict of dfs (key: df name; value: df)
def iterate_months(merged_event_dfs, months_back: int):
    states = []

    today = datetime.date.today()
    current_month_start = today.replace(day=1)

    for i in range(months_back):
        # shift month back by i
        year = current_month_start.year
        month = current_month_start.month - i

        while month <= 0:
            month += 12
            year -= 1

        month_start = datetime.date(year, month, 1)

        # compute month end
        next_month = month_start.replace(day=28) + datetime.timedelta(days=4)
        month_end = next_month - datetime.timedelta(days=next_month.day)

        states.append(
            get_state(
                merged_event_dfs,
                pd.to_datetime(month_start),
                pd.to_datetime(month_end),
            )
        )

    state_df = pd.DataFrame(states)
    state_df.columns = (col.title() for col in state_df.columns)
    return sort_df_by_date(state_df, "Month")

# %%
def export_to_excel(dataframe_sheets):
    with pd.ExcelWriter(excel_filename) as writer:
        keys_list = list(dataframe_sheets.keys())
        for sheet in dataframe_sheets:
            dataframe_sheets[sheet].to_excel(writer, sheet_name=sheet, index=keys_list.index(sheet))

# %%
def get_frequent_expenses(expenses_df):
    value_counts = expenses_df[description].value_counts()
    expenses_df[date] = pd.to_datetime(expenses_df[date])
    cutoff_date = datetime.datetime.now() - pd.DateOffset(months=lookback_months)
    expenses_df.loc[:, 'frequency'] = expenses_df[description].map(value_counts).astype(int)
    recent_frequented_merchants = expenses_df.loc[(expenses_df['frequency'] > 1) & (expenses_df[date] >= cutoff_date), description].drop_duplicates(ignore_index=True)
    return recent_frequented_merchants

# %%
def main():
    merged_transactions = merge_events(transaction_path, negate_cost=True)
    merged_banking = merge_events(banking_path, negate_cost=False)
    merged_coc = merge_events(cap_one_path, negate_cost=False)
    merged_hysa = merge_events(hysa_path, negate_cost=False)
    merged_transactions = enrich_grocery(merged_transactions)

    merged_event_dfs = {
        "transactions" : merged_transactions, 
        "banking" : merged_banking, 
        "coc" : merged_coc, 
        "hysa" : merged_hysa
    }

    date_start = pd.to_datetime(datetime.date.today() - relativedelta(months=lookback_months)).replace(day=1)
    date_end = pd.to_datetime(datetime.date.today())

    net_df = iterate_months(merged_event_dfs, lookback_months)
    
    merged_all = merge_cash_flow(merged_event_dfs)
    
    filtered_all = filter_events_by_date(date_start, date_end, merged_all)
    income_df, expenses_df = get_cash_flow(filtered_all)
    
    if merch_intel:
        transaction_intel_df = merchant_intelligence.build_merchant_intel(expenses_df[description], local_merch_intel_filename)
        expenses_df = expenses_df.merge(
            transaction_intel_df[['domain', 'handle', 'type', 'name', 'founded', 'industry', 'size', 'hq_city', 'hq_state', 'hq_state_code', 'hq_country_code', 'transaction']],
            left_on=description,
            right_on='transaction',
            how='left'
        ).drop(columns=['transaction']).drop_duplicates()
        print("Merchant intelligence successfully executed:", merchant_intelligence_filename)
        print("Merchant Intelligence Coverage: ", float(len(transaction_intel_df) / len(expenses_df)).__round__(2))
    
    fixed_expenses_df, variable_expenses_df, discretionary_expenses_df = define_expenses(expenses_df)

    if excel == True:
        dataframe_sheets = {
            "Net" : net_df,
            "Fixed Expenses" : fixed_expenses_df,
            "Variable Expenses" : variable_expenses_df,
            "Discretionary Expenses" : discretionary_expenses_df,
            "All Transactions" : merged_transactions,
            "All Banking" : merged_banking,
            "All Cap One Checking" : merged_coc,
            "All HYSA" : merged_hysa
        }
        try:
            export_to_excel(dataframe_sheets)
        except Exception as e:
            print("Failed to create Excel file:", e)
        else:
            print("Excel file created successfully.", excel_filename)
    return transaction_intel_df, expenses_df

# %%
if __name__ == "__main__":
    transaction_intel_df, expenses_df = main()

# %%
# date_start = pd.to_datetime(datetime.date.today() - relativedelta(months=8)).replace(day=1)
# date_end = pd.to_datetime(datetime.date.today())

# merged_transactions = merge_events(transaction_path, negate_cost=True)
# merged_banking = merge_events(banking_path, negate_cost=False)
# merged_coc = merge_events(coc_path, negate_cost=False)
# merged_hysa = merge_events(hysa_path, negate_cost=False)
# merged_transactions = enrich_grocery(merged_transactions)

# merged_event_dfs = {
#     "transactions" : merged_transactions, 
#     "banking" : merged_banking, 
#     "coc" : merged_coc, 
#     "hysa" : merged_hysa
# }

# merged_all = merge_cash_flow(merged_event_dfs)

# filtered_all = filter_events_by_date(date_start, date_end, merged_all)
# income_df, expenses_df = get_cash_flow(filtered_all)

# transaction_intel_df = merchant_intelligence.build_merchant_intel(expenses_df[description], local_merch_intel_filename)
# expenses_df = expenses_df.merge(
#     transaction_intel_df,
#     left_on=description,
#     right_on='transaction',
#     how='left'
# ).drop(columns=['transaction']).drop_duplicates()



