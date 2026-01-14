# %%
import requests
import pandas as pd
import trove_key
import datetime

# %%
def get_merchant_info(transaction_data):
    url = "https://trove.headline.com/api/v1/transactions/enrich"
    headers = {
        'X-API-KEY': trove_key.TROVE_KEY,
        'content-type': 'application/json'
    }
    return requests.post(url, json=transaction_data, headers=headers)

# %%
def build_merchant_intel(recent_frequented_merchants, local_merch_intel_filename):
    with open(local_merch_intel_filename, 'w') as file:
        merch_intel_cols = ['domain', 'categories', 'handle', 'type', 'name', 'founded', 'industry', 'size', 'hq_city', 'hq_state', 'hq_state_code', 'hq_country_code', 'summary', 'transaction']
        try:
            local_merch_intel_df = pd.read_csv(file, usecols=merch_intel_cols)
        except: # If file does not exist
            local_merch_intel_df = pd.DataFrame(columns=merch_intel_cols)
        for merchant in recent_frequented_merchants:
            if not merchant in local_merch_intel_df['transaction']:
                transaction_data = {
                    "description" : merchant,
                    "amount" : "1.00",
                    "date" : datetime.datetime.now().strftime('%Y-%m-%d'),
                    "user_id" : "user_id"
                }
                merchant_intel = get_merchant_info(transaction_data).json()
                if merchant_intel['domain']:
                    merchant_intel['transaction'] = merchant_intel['query']['description']
                    merchant_intel.pop('query')
                    merchant_intel_df = pd.DataFrame(merchant_intel, columns=merch_intel_cols)
                    local_merch_intel_df = pd.concat([local_merch_intel_df, merchant_intel_df])
        local_merch_intel_df.to_csv(local_merch_intel_filename)


