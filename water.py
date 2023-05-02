import pandas as pd

from flask import Flask, render_template, request


# Load the data from the Excel file
url = 'https://www.vanduo.lt/uploads/Vandens%20kokyb%C4%97/2023%20m.%20kovo%20m%C4%97n.%20patiekto%20geriamojo%20vandens%20kokyb%C4%97.xlsx'
df = pd.read_excel(url, sheet_name=0, skiprows=3, usecols=[2] + list(range(7, 26)), nrows=43)

# Rename columns to match the excel column letters
df = df.rename(columns={col: chr(col_num + 65) for col_num, col in enumerate(df.columns)})


# print(df.loc[1, 'B'])

# Keep the places column (C7-47) non-numeric
df.loc[6:42, 'A'] = df.loc[6:42, 'A'].astype(str)


# Replace <,> signs with nothing and replace , with .
df.loc[1:42, 'B':'X'] = df.loc[1:42, 'B':'X'].replace({'<': '', '>': '', ',': '.'}, regex=True)



# Replace non-numeric values with NaN for subset of columns H to Z (rows 7-47)
df.loc[1:42, 'B':'X'] = df.loc[1:42, 'B':'X'].apply(pd.to_numeric, errors='coerce')



# Replace NaN values with 0
df = df.fillna(0)

# print(df)


# extract the standard parameter row and drop column A
standard_params = df.iloc[1,1:].values

# print the standard parameter values
print("Standard Parameters:")
print(standard_params)

params_dict = dict(zip(df.iloc[0,1:], df.iloc[1,1:]))

print(params_dict)

import numpy as np


df.replace(0, np.nan, inplace=True) # Replace 0 with NaN


# print(df)

recommended_parameters = {'Amonis, mg/l': 0.5,
                          'Fluoridai, mg/l': 0.5,
                          'Nitritas, mg/l': 0.5,
                          'Nitratas, mg/l': 10.0,
                          'Bendroji geležis, μg/l': 200.0,
                          'Manganas, μg/l': 50.0,
                          'Boras, mg/l': 1.5,
                          'Permang.indeksas, O2 mg/l': 5.0,
                          'Chloridai, mg/l': 200.0,
                          'Sulfatai, mg/l': 250.0,
                          'Natris, mg/l': 200.0,
                          'Bendras kietumas, mmol/l': '-',
                          'Aliuminis, mg/l': 200.0,
                          'Kadmis, mg/l': 3.0,
                          'Nikelis, mg/l': 20.0,
                          'Varis, mg/l': 1.3,
                          'Koliforminių bakterijų sk.': 1.0,
                          'Žarninių lazdelių sk.': 1.0,
                          'Žarninių enterokokų sk.': 1.0}

# create a new row with recommended parameter values
new_row = pd.DataFrame([["Rekomendacija"] + list(recommended_parameters.values())], columns=df.columns, index=[len(df)])
# append the new row to the dataframe
df = df.append(new_row)

df.replace("-", np.nan, inplace=True) # Replace "-" with NaN

print(df)


# extract the watering place names
watering_places = list(df.loc[2:42, 'A'].values)

# print (watering_places)




app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    watering_places = df.iloc[2:43, 0].tolist()  # Get the list of watering places
    return render_template('home.html', watering_places=watering_places)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/water-parameters')
def water_parameters():
    # Get the selected watering place from the request parameters
    watering_place = request.args.get('watering_place')

    # Get the parameter names and values for the selected watering place
    parameter_names = df.loc[0, 'B':'T']
    parameter_values = df.loc[df['A'] == watering_place, 'B':'T'].values.flatten().tolist()
    

    # Extract standard and recommended values from the DataFrame
    standard = list(df.loc[1, 'B':'T'])
    recommended = list(df.loc[43, 'B':'T'])

    # Calculate deviation of parameter values from standard and recommended values
    deviation_from_standard = []
    deviation_from_recommended = []
    for i in range(len(parameter_names)):
        value = parameter_values[i]
        std = standard[i]
        rec = recommended[i]
        if pd.isna(value):
            deviation_from_standard.append(None)
            deviation_from_recommended.append(None)
        elif pd.isna(std) or pd.isna(rec):
            deviation_from_standard.append(None)
            deviation_from_recommended.append(None)
        else:
            deviation_from_standard.append(round(value - std, 2))
            deviation_from_recommended.append(round(value - rec, 2))

    # Calculate deviation of parameter values from standard and recommended values and replacing None with -
    # deviation_from_standard = []
    # deviation_from_recommended = []
    # for i in range(len(parameter_names)):
    #     value = parameter_values[i]
    #     std = standard[i]
    #     rec = recommended[i]
    #     if pd.isna(value):
    #         deviation_from_standard.append("-")
    #         deviation_from_recommended.append("-")
    #     elif pd.isna(std) or pd.isna(rec):
    #         deviation_from_standard.append("-")
    #         deviation_from_recommended.append("-")
    #     else:
    #         std_deviation = round(value - std, 2)
    #         rec_deviation = round(value - rec, 2)
    #         deviation_from_standard.append(str(std_deviation) if std_deviation else "-")
    #         deviation_from_recommended.append(str(rec_deviation) if rec_deviation else "-")


    # Add color coding to the deviation values
    def color_code(deviation, value, standard, recommended, is_recommended=False):
        if deviation is None:
            return ''
        elif is_recommended and value <= recommended:
            return 'green'
        elif is_recommended and value > recommended:
            return 'red'
        elif value <= standard:
            return 'green'
        elif value > standard:
            return 'red'
        


    deviation_from_standard_colors = [color_code(deviation, value, standard[i], recommended[i], False) for i, (deviation, value) in enumerate(zip(deviation_from_standard, parameter_values))]
    deviation_from_recommended_colors = [color_code(deviation, value, standard[i], recommended[i], True) for i, (deviation, value) in enumerate(zip(deviation_from_recommended, parameter_values))]
    
    # Replacing nan with -
    parameter_values = ['-' if pd.isna(value) else value for value in parameter_values]
    standard = ["-" if pd.isna(val) else val for val in standard]
    recommended = ["-" if pd.isna(val) else val for val in recommended]


    return render_template('water_parameters.html', 
                           watering_place=watering_place, 
                           parameter_names=parameter_names, 
                           parameter_values=parameter_values,
                           standard=standard,
                           recommended=recommended,
                           deviation_from_standard=deviation_from_standard,
                           deviation_from_standard_colors=deviation_from_standard_colors,
                           deviation_from_recommended=deviation_from_recommended,
                           deviation_from_recommended_colors=deviation_from_recommended_colors)



if __name__ == '__main__':
     app.run(debug=True, port=8080)