	function myDateTick(t,sFrequency,iDateStr,fLimits); 
	
	[y,m,d,h,mn,s]=mydatevec(t); 
	iYrs=unique(y); 
	iSerMos=(y-1)*12+m; 
	iSerMo1=min(iSerMos); iSerMo2=max(iSerMos); 
	nSerMos=iSerMo2-iSerMo1+1; 

	xDates=[]; 
	switch sFrequency
		case 'Dy'; 
			xDates=t(1:48:end); 
		case '2Dy'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end; 
			for iDy=1:2:29; xDates=[xDates datenum(iYr1,iMo1:(iMo1+nSerMos),iDy)]; end; 	
		case '3Dy'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end; 
			for iDy=1:3:28; xDates=[xDates datenum(iYr1,iMo1:(iMo1+nSerMos),iDy)]; end; 	
		case '5Dy'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end; 
			for iDy=1:5:26; xDates=[xDates datenum(iYr1,iMo1:(iMo1+nSerMos),iDy)]; end; 	
		case '7Dy'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end; 
			for iDy=1:7:22; xDates=[xDates datenum(iYr1,iMo1:(iMo1+nSerMos),iDy)]; end; 	
		case '10Dy'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end; 
			for iDy=1:10:21; xDates=[xDates datenum(iYr1,iMo1:(iMo1+nSerMos),iDy)]; end; 	
		case '14Dy'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end; 
			for iDy=1:14:15; xDates=[xDates datenum(iYr1,iMo1:(iMo1+nSerMos),iDy)]; end; 	
		case '15Dy'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end; 
			for iDy=1:15:16; xDates=[xDates datenum(iYr1,iMo1:(iMo1+nSerMos),iDy)]; end; 	
		case 'Mo'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end;
			xDates=datenum(iYr1,iMo1:(iMo1+nSerMos),1); 
% % % 			datestr(xDates)
% % % 			datestr([min(t) max(t)])
% % % 			pause; 
		case '2Mo'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end;
			xDates=datenum(iYr1,iMo1:2:(iMo1+nSerMos),1);
		case '3Mo'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end;
			xDates=datenum(iYr1,iMo1:3:(iMo1+nSerMos),1);
		case '4Mo'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end;
			xDates=datenum(iYr1,iMo1:4:(iMo1+nSerMos),1);
		case '6Mo'; 
			iYr1=floor(iSerMo1/12)+1; iMo1=mod(iSerMo1,12); if iMo1==0; iMo1=12; iYr1=iYr1-1; end;
			xDates=datenum(iYr1,iMo1:6:(iMo1+nSerMos),1);
		case 'Yr'; 
			iYr1=min(iYrs); iYr2=max(iYrs); 
			xDates=datenum(iYr1:iYr2+1,1,1); 
	end; 
	xDates=unique(xDates); 
	set(gca,'xTick',xDates); set(gca,'xTickLabel',[]); 
	if iDateStr>0; 
		cDates=datestr(xDates,iDateStr); 
		set(gca,'xTickLabel',cDates); 
	end; 	
	if fLimits==1; 
		xlim([floor(min(xDates)) ceil(max(xDates))]); 
		grid on; box on; 
	end; 
	
	
		
		