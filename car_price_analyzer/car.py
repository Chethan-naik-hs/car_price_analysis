import pandas as pd
import numpy as np

# Load your CSV file
df = pd.read_csv("uploads/car_prices.csv")

# Add 'buyers' column with random values
df['buyers'] = np.random.choice(['officials', 'businessman', 'farmer'], size=len(df))

# Function to get vehicle name
def get_vehicle_name(make, model):
    if isinstance(make, str) and make.lower() == 'ford':
        if isinstance(model, str):
            if 'ecosport' in model.lower():
                return 'EcoSport, a compact SUV'
            elif 'endeavour' in model.lower():
                return 'Endeavour'
    return 'Unknown'

# Apply the function
df['vehicle_name'] = df.apply(lambda row: get_vehicle_name(row['make'], row['model']), axis=1)

# Save the updated file
df.to_csv("updated_car_prices.csv", index=False)
