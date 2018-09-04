	function [Cp2,s2,Cp3,s3] = cpdFindChangePoint20100901(xx,yy,fPlot,cPlot) 
	
%cpdFindChangePoint20100901
%
%is an operational version of the Lund and Reeves (2002) 
%change-point detection algorithm as modified and 
%implemented by Alan Barr for uStarTh evaluation. 
%
%Syntax: 
%
%[Cp2,s2,Cp3,s3] = cpdFindChangePoint20100901(uStar,NEE,fPlot,Txt)
%
%- Cp2 changepoint (uStarTh) from operational 2-parameter model, 
%- Cp3 changepoint (uStarTh) from diagnostic 3-parameter model, 
%- s2 structured record containing statistics from Cp2 evaluation, 
%- s3 structured record containing statistics from Cp3 evaluation
%
%- xx,yy variables for change-point detection
%- fPlot flag set to 1 to plot 
%- cPlot text string for plot title
%
%Note: The individual variables Cp2 and Cp3 are set to NaN if not significant
%but the values s2.Cp and s3.Cp are retained even if not significant.

%	=======================================================================
%	=======================================================================

%	Functions called:
%	- cpdFmax2pCp2,cpdFmax2pCp3
%	from stats toolbox - regress

%	Written by Alan Barr, last updated 7 Oct 2010 

%	=======================================================================
%	=======================================================================

%	Initialize outputs. 

	Cp2=NaN; Cp3=NaN;  
	
	s2=[]; s2.n=NaN; s2.Cp=NaN; s2.Fmax=NaN; s2.p=NaN; 
	s2.b0=NaN; s2.b1=NaN; s2.b2=NaN; s2.c2=NaN; 
	s2.cib0=NaN; s2.cib1=NaN; s2.cic2=NaN; 
	s3=s2; 	
	
%	=======================================================================
%	=======================================================================

%	Exclude missing data. 

	x=reshape(xx,length(xx),1); y=reshape(yy,length(yy),1); 
	iNaN=find(isnan(x+y)); x(iNaN)=[]; y(iNaN)=[]; 
	n=length(x+y); if n<10; return; end;

%	Exclude extreme lin reg outliers. 

	a = [ones(n,1) x] \ y; yHat = a(1) + a(2)*x; 
	dy=y-yHat; mdy=mean(dy); sdy=std(dy); 
	ns=4; iOut=find(abs(dy-mdy)>ns*sdy); x(iOut)=[]; y(iOut)=[]; 

	n=length(x+y); if n<10; return; end;

%	Compute statistics of reduced (null hypothesis) models
%	for later testing of Cp2 and Cp3 significance.  
	
	yHat2=mean(y); SSERed2=sum((y-yHat2).^2); 
	a = [ones(n,1) x] \ y; yHat3 = a(1) + a(2)*x; SSERed3=sum((y-yHat3).^2); 
	nRed2=1; nFull2=2; nRed3=2; nFull3=3; 
	
%	Compute F score (Fc2 and Fc3) for each data point 	
%	in order to identify Fmax.

	MT=NaN*ones(n,1); Fc2=MT; Fc3=MT; 
	
	nEndPtsN=3; nEndPts=floor(0.05*n); 
	if nEndPts<nEndPtsN; nEndPts=nEndPtsN; end; 
	
	for i=1:(n-1); % min of 1 points at either end (was nEndPts before 20100318)
		
		% fit operational 2 parameter model, with zero slope above Cp2: 
		% 2 connected line segments, segment 2 has zero slope
		% parameters b0, b1 and xCp
		
		iAbv=(i+1):n; 
		x1=x; x1(iAbv)=x(i); 
		a2 = [ones(n,1) x1]\y; 
		yHat2 = a2(1) + a2(2)*x1; 
		SSEFull2=sum((y-yHat2).^2); 
		Fc2(i)=(SSERed2-SSEFull2)/(SSEFull2/(n-nFull2)); 
		
		% fit diagnostic 3 parameter model, with non-zero slope above Cp2: 
		% 2 connected line segments with noslope constraints 
		% parameters b0, b1, b2 and xCp
		
		zAbv=zeros(n,1); zAbv(iAbv)=1; 
		x1=x; x2=(x-x(i)).*zAbv; 
		a3=[ones(n,1) x1 x2]\y; 
		yHat3 = a3(1) + a3(2)*x1 + a3(3)*x2; 
		SSEFull3=sum((y-yHat3).^2); 
		Fc3(i)=(SSERed3-SSEFull3)/(SSEFull3/(n-nFull3)); 

	end; 
	
%	Assign changepoints from Fc2 and Fc3 maxima. 
%	Calc stats and test for significance of Fmax scores.

	pSig=0.05; 

	[Fmax2,iCp2]=max(Fc2); xCp2=x(iCp2);
	iAbv=(iCp2+1):n; x1=x; x1(iAbv)=xCp2;
	[a2,a2int]=regress(y,[ones(n,1) x1]);
	yHat2 = a2(1) + a2(2)*x1;
	p2=cpdFmax2pCp2(Fmax2,n); 
	Cp2=xCp2; if p2>pSig; Cp2=NaN; end;
	
	[Fmax3,iCp3]=max(Fc3); xCp3=x(iCp3);
	iAbv=(iCp3+1):n; zAbv=zeros(n,1); zAbv(iAbv)=1;
	x1=x; x2=(x-xCp3).*zAbv;
	[a3,a3int]=regress(y,[ones(n,1) x1 x2]);
	yHat3 = a3(1) + a3(2)*x1 + a3(3)*x2;
	p3=cpdFmax2pCp3(Fmax3,n); 
	Cp3=xCp3; if p3>pSig; Cp3=NaN; end;
	
%	Assign values to s2, but only if not too close to end points.  	
	
	s2.n=n; s3.n=n; 
	
	if iCp2>(nEndPts) & iCp2<(n-nEndPts);
		
		b0=a2(1); cib0=0.5*diff(a2int(1,:)); 
		b1=a2(2); cib1=0.5*diff(a2int(2,:));
		
		s2.Cp=Cp2; s2.Fmax=Fmax2; s2.p=p2; 
		s2.b0=b0; s2.b1=b1; s2.b2=NaN; s2.c2=NaN;
		s2.cib0=cib0; s2.cib1=cib1; s2.cic2=NaN;
		
	end;
	
	if iCp3>(nEndPts) & iCp3<(n-nEndPts);
		
		b0=a3(1); cib0=0.5*diff(a3int(1,:)); 
		b1=a3(2); cib1=0.5*diff(a3int(2,:));
		b2=a3(3); cic2=0.5*diff(a3int(3,:));
		c2=a3(2)+a3(3);
		
		s3.Cp=xCp3; s3.Fmax=Fmax3; s3.p=p3; 
		s3.b0=b0; s3.b1=b1; s3.b2=b2; s3.c2=c2;
		s3.cib0=cib0; s3.cib1=cib1; s3.cic2=cic2;
		
	end;
	
%	=======================================================================
%	=======================================================================
	
	if fPlot==1;
		
		cla; hold on; 
		plot(x,y,'ko','MarkerFaceColor','k'); 
		plot(x,yHat2,'r-','linewidth',2); 
		plot(x,yHat3,'g-','linewidth',2); 
		plot([xCp2 xCp2],[min(y) max(y)],'r-','linewidth',2); 
		plot([xCp3 xCp3],[min(y) max(y)],'g-','linewidth',2); 
		hold off; grid on; box on; 
		
		if a2(2)>0; cMode='D'; else cMode='E'; end; 
		title(sprintf('%s %5.3f %s',cPlot,Cp2,cMode)); 
		
		xX=max(x)*1.02; if xX>0; xlim([0 xX]); end;
		yN=min(y); yX=max(y); dy=yX-yN; 
		yN=yN-0.02*dy; yX=yX+0.02*dy;
		if yN<yX; ylim([yN yX]); end; 
		
		set(gca,'FontSize',10);

	end;
	
%	=======================================================================
%	=======================================================================

