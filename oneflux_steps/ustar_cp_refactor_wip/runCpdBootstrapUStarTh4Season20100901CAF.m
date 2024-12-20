%	runCpdBootstrapUStarTh4Season20100901CAF

	myccc; warning off; 

	[Sites8 Sites5ca] = GetNACPCCPSites; 
	[DirsSub Sites8 Sites5us] = GetNACPAmerifluxSites; 

	Sites=sort([myrv(Sites5ca) myrv(Sites5us)]); 
	nSites=length(Sites); 
	
	nBoot=1000; cnBoot=num2str(nBoot); 
	
	DirCp=['i:\Ameriflux\uStarThAnalysis20100901\Annual\Merged\Boot' cnBoot '\']; mkdir(DirCp); 
	DirJpg=[DirCp 'figures\']; mkdir(DirJpg); 
	DirMerged='i:\Ameriflux\nacpL234.Merged\'; 
	
	disp(' '); disp(' '); 

%	========================================================================
%	========================================================================
	
	for iSite=1:nSites;
		
		try;
			
			cSite=char(Sites(iSite));
			
			t=[]; Ta=[]; Ts=[]; Rsd=[]; PPFD=[]; Fc=[]; NEE=[]; uStar=[];
			TaGF=[]; TsGF=[]; RsdGF=[];
			
			eval(['load ' DirMerged cSite '_Met&Flx;']);
			eval(['load ' DirMerged cSite '_NeeQC;']);
			iFilt=3; NEE=NeeQC(:,iFilt+1);
			
			if ~isempty(NEE);

				T=(TaGF+TsGF)/2; 
			
				nt=length(t); [y,m,d]=datevec(t);
				fNight=RsdGF<5; iNight=find(fNight); iDay=find(~fNight);
				iOut=find(uStar<0 | uStar>4); uStar(iOut)=NaN;
				
				nPerDay=round(1/nanmedian(diff(t)));
				
				nSeasonsN=4; nStrataN=4; nStrataX=8; nBins=50; nPerBin=5;
				switch nPerDay;
					case 24; nPerBin=3;
					case 48; nPerBin=5;
				end;
				nPerSeasonN=nStrataN*nBins*nPerBin; 
				ntN=nSeasonsN*nPerSeasonN;
				
				itNee=find(~isnan(NEE+uStar+T+PPFD));
				itNee=intersect(itNee,iNight);
				
				iYrs=myrv(unique(y));
				
				for iYr=iYrs;
					
					it=find(y==iYr); jtNee=intersect(it,itNee); njtNee=length(jtNee);
					
					if njtNee>=ntN; 
						
						cYr=num2str(iYr); 
						FileCp=[DirCp 'cpdBootstrap4Season20100901_Boot' cnBoot '_' cSite '-' cYr 'C.mat']; 
						
						if exist(FileCp)==2; 
								
								disp(' '); disp([cSite '-' cYr ' was already processed.']); disp(' '); 
								
							else; 
								
								[Cp2,Stats2,Cp3,Stats3] = ...
									cpdBootstrapuStarTh4Season20100901 ...
										(t(it),NEE(it),uStar(it),T(it),fNight(it),1,[cSite '-' cYr],nBoot);
									
								[aCp2,nCp2,tW2,CpW2,cMode2,cFailure2,fSelect2,sSine2,FracSig2,FracModeD2,FracSelect2] ...
									= cpdAssignUStarTh20100901(Stats2,1,[cSite '-' cYr]);
								FileJpg2=[DirJpg 'cpdBootstrap4Season20100901_Boot' cnBoot '_' cSite '-' cYr '_Model2C']; 
								eval(['print -djpeg100 ' FileJpg2 ';']);
							
								[aCp3,nCp3,tW3,CpW3,cMode3,cFailure3,fSelect3,sSine3,FracSig3,FracModeD3,FracSelect3] ...
									= cpdAssignUStarTh20100901(Stats3,1,[cSite '-' cYr]);
								FileJpg3=[DirJpg 'cpdBootstrap4Season20100901_Boot' cnBoot '_' cSite '-' cYr '_Model3C']; 
								eval(['print -djpeg100 ' FileJpg3 ';']);

								eval(['save ' FileCp ' Cp2 Cp3 Stats2 Stats3 ' ...
									'aCp2 nCp2 tW2 CpW2 cMode2 cFailure2 fSelect2 sSine2 FracSig2 FracModeD2 FracSelect2 '...
									'aCp3 nCp3 tW3 CpW3 cMode3 cFailure3 fSelect3 sSine3 FracSig3 FracModeD3 FracSelect3;']);
						
						end; % if exist(FileCp)=2;
						
					end; % if nit>=ntN;
					
				end; % for iYr=iYrs;
				
			end; % if ~isempty
			disp(' '); disp(' ');
			
		catch;
			disp(' '); disp(' ');
			disp('********************************************************');
			disp('********************************************************');
			disp(['Error trapped:  ' cSite '-' cYr]);
			disp(lasterr);
			disp('********************************************************');
			disp('********************************************************');
			disp(' '); disp(' ');
		end;
		
	end; % for iSite=1:nSites;
	
	
