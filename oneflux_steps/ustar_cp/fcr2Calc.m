	function r2=r2Calc(y,yHat);    
   
   n=length(y); ym=mean(y); 
   
   SSreg=sum((yHat-ym).^2); 
   SStotal=sum((y-ym).^2); 
   rmse=sum((yHat-y).^2); 
   r2=SSreg/SStotal; 
   
% % %    sprintf('%7.4f %7.4f %7.4f ',[SSreg SStotal r2 rmse]) 
   
