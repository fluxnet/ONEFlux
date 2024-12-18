	function r2=fcr2Calc(y,yHat);    
   
   % This function calculates the r^2 measure (coeffecient of determination)
   % for a pair of data `y` and some predicted `yHat`.
  
   n=length(y); ym=mean(y); 
   
   % explained sum of squares
   SSreg=sum((yHat-ym).^2); 

   % total sum of squares
   SStotal=sum((y-ym).^2); 

   rmse=sum((yHat-y).^2);  % Note this is redundant

   % coeffecient of determination
   r2=SSreg/SStotal; 
   
% % %    sprintf('%7.4f %7.4f %7.4f ',[SSreg SStotal r2 rmse]) 
   
