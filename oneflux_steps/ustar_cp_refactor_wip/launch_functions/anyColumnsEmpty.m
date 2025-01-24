function [errorCode] = anyColumnsEmpty(uStar, NEE, Ta, Rg)

    errorCode = 0;

    %         data_L3(data_L3==-9999)=NaN; data_L3(data_L3==-6999)=NaN;

    % by carlo, added by alessio on February 21, 2014
    if sum(isnan(NEE)) == numel(NEE); 
        fprintf('NEE is empty!\n');
        errorCode = 1;
        return;
    end
    if sum(isnan(uStar)) == numel(uStar); 
        fprintf('uStar is empty!\n');
        errorCode = 1;
        return;
    end
    if isempty(Ta); 
        fprintf('Ta is empty!\n');
        errorCode = 1;
        return;
    end
    if isempty(Rg); 
        fprintf('Rg is empty!\n');
        errorCode = 1;
        return;
    end
    
end