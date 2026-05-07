import pandas as pd

# Charger le CSV des transactions
df = pd.read_csv("output/transactions_clients.csv", sep=';', decimal=',', encoding='utf-8-sig')

print(" Colonnes disponibles :", df.columns.tolist())
print("\n operation_type uniques (non vides) :")
ops = df['operation_type'].dropna().unique()
print(sorted(ops))

print("\n code_autorisation uniques (non vides) :")
codes = df['code_autorisation'].dropna().unique()
print(sorted(codes))

print("\n transaction_type_id uniques (non vides) :")
tx_ids = df['transaction_type_id'].dropna().unique()
print(sorted(tx_ids))