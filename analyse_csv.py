import pandas as pd

df = pd.read_csv("output/transactions_clients.csv", sep=';', decimal=',', encoding='utf-8-sig')

print("=== COLONNES DISPONIBLES ===")
print(df.columns.tolist())

cols = ['operation_type', 'provider_id', 'receiver_id', 'transaction_type_id', 'code_autorisation']
for col in cols:
    if col in df.columns:
        uniq = df[col].dropna().unique()
        print(f"\n--- {col} ---")
        print(f"Nombre de valeurs uniques : {len(uniq)}")
        print(f"Exemples (jusqu'à 10) : {list(uniq)[:10]}")
    else:
        print(f"\n--- {col} : colonne absente ---")

# Vérifier s'il y a des receiver_id non nuls
if 'receiver_id' in df.columns:
    nb_receiver = df['receiver_id'].notna().sum()
    print(f"\nNombre de transactions avec receiver_id non nul : {nb_receiver}")
else:
    print("\nPas de colonne receiver_id")