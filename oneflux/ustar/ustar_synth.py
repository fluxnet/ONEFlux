
## -- ## --## -- ## --## -- ## -- ## -- ## -- ## --## -- ## -- ## -- ## -- ## -- ## -- ## -- ##
## -- ## --## -- ## --## -- ## -- ##  SYNTHETIC USTAR T  ## -- ## -- ## -- ## -- ## -- ## -- ## 
## -- ## --## -- ## --## -- ## -- ## -- ## -- ## --## -- ## -- ## -- ## -- ## -- ## -- ## -- ##

# Input: site folder path # 
# Output: synthetic USTAR threshold series, identycal to the real one # 
# Values are calculated from a set of linear model coefficient, provided externally #

def synth_ut(site_path):

    # -- PACKAGES IMPORT -- # 
    import os
    import pandas as pd
    import numpy as np
    from scipy import stats
    import shutil
    from terms import TERMS
    from io import StringIO

    # Paths # 
    QC_AUTO=os.path.join(site_path, "02_qc_auto")
    USTAR_SYNTH=os.path.join(site_path, "03_ustar_synth")
    USTAR_SYNTH_INPUT=os.path.join(site_path, "03_ustar_synth", "input")


    # -- USTAR INPUT FILE LIST -- #
    ustar_list=[file for file in os.listdir(QC_AUTO) if "ustar" in file]


    # -- SITE CODE -- #
    # Get the site code from the first USTAR file # 
    SITE_CODE=os.path.basename(ustar_list[0]).split('_')[0]


    # -- INPUT FOLDER -- #
    # Create the input folder where copy the QC_AUTO files # 
    if not os.path.exists(USTAR_SYNTH_INPUT):
        os.makedirs(USTAR_SYNTH_INPUT)

    # Copy the input files in the ustar input folder # 
    [shutil.copyfile(src=os.path.join(QC_AUTO, file), 
                    dst=os.path.join(USTAR_SYNTH_INPUT, file))
                    for file in ustar_list]


    # -- MODEL INPUT TERMS COLLECTION -- #
    terms=pd.read_csv(StringIO(TERMS))

    # Remove the 50th percentile # 
    terms=terms[terms['prob'] != 50]

    # Collect required terms # 
    terms_required = [s for s in terms.columns if 'term' in s]

    # Coefficients and intercept extraction #  
    coeffs = terms[terms_required].values
    intercept = terms['int'].values


    # -- USTAR VALUES STACK -- # 
    # Create an empty dataframe #
    df=pd.DataFrame()

    # Find the start line # 
    for p in ustar_list:
        with open(os.path.join(USTAR_SYNTH_INPUT, p) , 'r') as f:
            for i, line in enumerate(f):
                if 'TIMESTAMP' in line:
                    start_row = i
                    break
            
        # USTAR csv reading and merging #
        df=pd.concat([df, 
                      pd.read_csv(os.path.join(USTAR_SYNTH_INPUT, p), skiprows=start_row)])
            
    # remove -9999 and select ustar
    u_series=df.loc[df['USTAR'] != -9999, "USTAR"].copy()

    # Define quantile probs #
    PROBS=np.arange(1.25, 100, 2.5)/100
    N=len(PROBS)

    # Create an empty dictionary for input values #
    model_input_values = {}

    # Populate the dictionary # 
    # First term: USTAR # Calculate percentiles # 
    if 'u_term' in terms_required:
        model_input_values['u']=u_series.quantile(PROBS).to_numpy()

    # Additional terms: shape indices, one between kurtosis and skewness #  
    if 'skew_term' in terms_required:
        model_input_values['skew']=np.full(N, u_series.skew())
    elif 'kurt_term' in terms_required:
        model_input_values['kurt']=np.full(N, u_series.kurt())
    # elif (additional terms)

    # Bind everything togheter #
    model_input_stack = np.column_stack([model_input_values[t.replace('_term', '')] for t in terms_required])

    # Verifiy the number fo dimensions # 
    if(not model_input_stack.shape == coeffs.shape): 
        raise ValueError("Predictors and coefficients dimensions don't match");

    if(not model_input_stack.shape[0] == intercept.shape[0]): 
        raise ValueError("Predictors and intercept dimensions don't match");


    # -- USTAR PREDICTION -- # Multiple linear model # 
    prediction = np.sum(model_input_stack * coeffs, axis=1) + intercept


    # -- QUANTILE STRETCHING -- #
    REPS=[3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 2, 3, 2, 
        3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3]
    synthetic_ut=prediction.repeat(REPS)


    # -- OUTPUT FILE WRITING -- #
    # If the values are the same of the originals, save the output file # 
    if(prediction in np.quantile(synthetic_ut, PROBS)):
        np.savetxt(os.path.join(USTAR_SYNTH, SITE_CODE + '_ut_synthetic.txt'), 
                    synthetic_ut, fmt='%.8f')
    else: 
        raise ValueError("Prediction and repetition array don't match");

    # END # 