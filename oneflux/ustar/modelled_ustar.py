
'''
MODELLED USTAR THRESHOLD ESTIMATION

This function calculates the modelled ustar threhsold values starting from a set of predictors and coefficents by applying a linear model on input data
Each ustar threhsold percentile has his own model, resulting in a total of 41 different models 

Input: site folder path, site ID # From site folder path import the yearly input data as csv tables 
Output: modelled USTAR threshold series calcualted both overall and by year, identycal in the file structure to the real one 

Base model: ustar threhsold = ustar * ustar_slope + intercept
Multiple model: ustar threhsold = ustar * ustar_slope + predictor 2 * slope 2 + ... + intercept

Additional predictors and coefficients can be added as columns in the inputs csv files and in the terms file, respectively
Eventual additional coefficients in the term file have to be named adding the suffix _slope

'''

def modelled_ut(site_id, site_path):

    ## -- PACKAGES IMPORT -- ## 

    import os
    import pandas as pd
    import numpy as np
    from scipy import stats
    import shutil
    from io import StringIO


    ## -- DEFINE PATHS -- ## 

    # QC auto path # 
    QC_AUTO=os.path.join(site_path, "02_qc_auto") 
    
    # Modelled ustar path #
    USTAR_MODELLED=os.path.join(site_path, "03_ustar_md") 

    # Inside modelled ustar, input csv tables #
    USTAR_MODELLED_INPUT=os.path.join(site_path, "03_ustar_md", "input")  
    
    # Path of the coefficients csv # 
    TERMS_PATH=os.path.dirname(__file__) 


    ## -- USTAR INPUT FILE LIST -- ##
    
    # These files contains the data of input predictors #
    ustar_list=[file for file in os.listdir(QC_AUTO) if "ustar" in file]


    ## -- SITE ID CHECK -- ## 
    
    # If is null, stop #
    if site_id is None:
        raise ValueError("Site ID must be provided")
    

    ## -- PERCENTILES -- ## 

    # Calculate the percentiles # 40 plus the median #
    PERC=np.append(np.arange(1.25, 100, 2.5), 50) 
    N=len(PERC)


    # -- INPUT FOLDER -- #
    # Create the input folder where copy the QC_AUTO files # 
    if not os.path.exists(USTAR_MODELLED_INPUT):
        os.makedirs(USTAR_MODELLED_INPUT)

    # Copy the input files in the ustar input folder # 
    [shutil.copyfile(src=os.path.join(QC_AUTO, file), 
                    dst=os.path.join(USTAR_MODELLED_INPUT, file))
                    for file in ustar_list]


    ## -- MODEL INPUT TERMS COLLECTION -- ##
    
    # The input term file must contain the model coefficients (at least one slope and the intercept) for each percentile 
    # In case of multiple linear models, the slope of each additional parameter must be added with the suffix _slope
    # The intercept column is always one
    terms=pd.read_csv(os.path.join(TERMS_PATH, "terms.txt"))

    # Get term(s) and intercept names #
    terms_required = [s for s in terms.columns if 'slope' in s]
    int_name = [s for s in terms.columns if 'intercept' in s]

    # In the output file the median is the last value # 
    # Ensure the same order between the percentiles in the term object and in the input data object # 
    terms=terms.set_index('percentile').loc[pd.Series(PERC)].reset_index()

    # Coefficients and intercept values extraction #  
    coeffs = terms[terms_required].values
    intercept = terms[int_name].values


    ## -- USTAR VALUES STACK -- ## 
    
    # Create an empty dataframe #
    df=pd.DataFrame()

    # Find the start line # In the input ustar file is needed to skip some rows # Identify the first one with the string 'TIMESTAMP'
    for p in ustar_list:
        with open(os.path.join(USTAR_MODELLED_INPUT, p) , 'r') as f:
            for i, line in enumerate(f):
                if 'TIMESTAMP' in line:
                    start_row = i
                    break
            
        # Define a temporary file and read it, starting from the 'TIMESTAMP' row previously identified
        tmp = pd.read_csv(os.path.join(USTAR_MODELLED_INPUT, p), skiprows=start_row)

        # Assign the year from the filename # 
        tmp["year"] = int(p.rsplit(".", 1)[0].split("_")[-1])

        # USTAR csv merging #
        df=pd.concat([df, tmp], ignore_index=True)


    ## -- USTAR THRESHOLD PREDICTION -- ## 
    
    # Loop over the years and the full dataset (identified as 'None')
    for y in np.append(df['year'].unique(), None):

        # Filter the full dataset by year or not (y==None: True)
        # remove -9999 values, select ustar and years
        if y == None:
            u_series=df.loc[(df['USTAR'] != -9999), "USTAR"].copy()
        else: 
            u_series=df.loc[(df['USTAR'] != -9999) & (df['year'] == y), "USTAR"].copy()


        ## -- INPUT PREDICTORS FINAL DICTIONARY -- ## 
        # A dictionary with the predictor values to use in the model #      
        # Create an empty dictionary #
        model_input_values = {}

        # Populate the dictionary # 
        # First term: USTAR # If the corresponding slope is listed in the coefficients, Calculate percentiles as for the ustar threshold 
        if 'ustar_slope' in terms_required:
            model_input_values['ustar']=u_series.quantile(PERC/100).to_numpy()

        # Eventual additional predictors to use togheter with ustar # 
        # Shape indices, one between kurtosis and skewness #  
        if 'skewness_slope' in terms_required:
            model_input_values['skewness']=np.full(N, u_series.skew())
        elif 'kurtosis_slope' in terms_required:
            model_input_values['kurtosis']=np.full(N, u_series.kurt())
        # elif (additional terms)
        # If, besides the overall intercept, only the ustar slope is in the coefficient list, a single linear model is computed using the percentiles derived from the u.series
        # When in the coefficient file there are more slopes, the predictors have to match them # In this case, the relation become a multiple linear regression

        # Bind everything togheter # Store the input predictors in a single np array
        model_input_stack = np.column_stack([model_input_values[t.replace('_slope', '')] for t in terms_required])

        # Verifiy the match of the number of dimensions between coefficients and input predictors # 
        if(not model_input_stack.shape == coeffs.shape): 
            raise ValueError("Predictors and coefficients dimensions don't match");

        # Verifiy the match of the number of rows between intercept and input predictors # The intercept is always one # 
        if(not model_input_stack.shape[0] == intercept.shape[0]): 
            raise ValueError("Predictors and intercept dimensions don't match");


        ## -- USTAR PREDICTION -- ## 
        
        # Potential multiple linear model # Sum every product between the slope and its corresponding predictor, then add the intercept #
        prediction = np.sum(model_input_stack * coeffs, axis=1, keepdims=True) + intercept


        ## -- OUTPUT FILE WRITING -- ##
        
        # Write a file for each 
        if y == None:
            np.savetxt(os.path.join(USTAR_MODELLED, site_id + '_usmd_all.txt' + '.txt'), prediction, fmt='%.8f')
        else: 
            np.savetxt(os.path.join(USTAR_MODELLED, site_id + '_usmd_' + str(y) + '.txt'), prediction, fmt='%.8f')

        # END # 