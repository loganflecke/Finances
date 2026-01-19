# %%
import requests
import pandas as pd
import trove_key
import datetime

# %%
def get_merchant_info(merchant):
    transaction_data = {
        "description" : merchant,
        "amount" : "1.00",
        "date" : datetime.datetime.now().strftime('%Y-%m-%d'),
        "user_id" : "user_id"
    }
    url = "https://trove.headline.com/api/v1/transactions/enrich"
    headers = {
        'X-API-KEY': trove_key.TROVE_KEY,
        'content-type': 'application/json'
    }
    return requests.post(url, json=transaction_data, headers=headers)

# %%
def build_merchant_intel(merchants : list[str], local_merch_intel_filename):
    merch_intel_cols = ['domain', 'categories', 'handle', 'type', 'name', 'founded', 'industry', 'size', 'hq_city', 'hq_state', 'hq_state_code', 'hq_country_code', 'summary', 'transaction']
    try:
        local_merch_intel_df = pd.read_csv(local_merch_intel_filename, usecols=merch_intel_cols)
    except: # If file does not exist or the custom 'transaction' column is not present
        local_merch_intel_df = pd.DataFrame(columns=merch_intel_cols)
    for merchant in merchants:
        if len(local_merch_intel_df.loc[local_merch_intel_df['transaction'] == merchant]) == 0:
            print(f"Making API call for {merchant}")
            merchant_intel = get_merchant_info(merchant)
            if merchant_intel.status_code != 200:
                print(f"- {merchant} returned no data")
                break
            else:
                merchant_intel = merchant_intel.json()
            try:
                merchant_intel['transaction'] = merchant_intel['query']['description']
                merchant_intel.pop('query')
                merchant_intel["categories"] = merchant_intel["categories"] or None
                merchant_intel_df = pd.DataFrame([merchant_intel], columns=merch_intel_cols).explode("categories")
                local_merch_intel_df = pd.concat([local_merch_intel_df, merchant_intel_df])
            except Exception as e:
                print(e)
                print(merchant_intel)
    local_merch_intel_df = local_merch_intel_df.sort_values(by='domain', ignore_index=True).drop_duplicates()
    local_merch_intel_df.to_csv(local_merch_intel_filename)
    return local_merch_intel_df

# %%
# merchants = ["STARBUCKS"]
# local_merch_intel_filename = "local_merch_intel.csv"
# merch_intel_cols = ['domain', 'categories', 'handle', 'type', 'name', 'founded', 'industry', 'size', 'hq_city', 'hq_state', 'hq_state_code', 'hq_country_code', 'summary', 'transaction']
# try:
#     local_merch_intel_df = pd.read_csv(local_merch_intel_filename, usecols=merch_intel_cols)
# except: # If file does not exist or the custom 'transaction' column is not present
#     local_merch_intel_df = pd.DataFrame(columns=merch_intel_cols)
# for merchant in merchants:
#     if len(local_merch_intel_df.loc[local_merch_intel_df['transaction'] == merchant]) == 0:
#         print(f"Making API call for {merchant}")
#         merchant_intel = get_merchant_info(merchant)
#         if merchant_intel.status_code != 200:
#             print(f"- {merchant} returned no data")
#             break
#         else:
#             merchant_intel = merchant_intel.json()
#         try:
#             merchant_intel['transaction'] = merchant_intel['query']['description']
#             merchant_intel.pop('query')
#             merchant_intel["categories"] = merchant_intel["categories"] or None
#             merchant_intel_df = pd.DataFrame([merchant_intel], columns=merch_intel_cols).explode("categories")
#             local_merch_intel_df = pd.concat([local_merch_intel_df, merchant_intel_df])
#             local_merch_intel_df = local_merch_intel_df.sort_values(by='domain', ignore_index=True)
#         except Exception as e:
#             print(e)
#             print(merchant_intel)


