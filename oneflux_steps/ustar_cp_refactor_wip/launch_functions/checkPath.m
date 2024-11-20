function [input_folder, output_folder] = checkPath(input_folder, output_folder)

    % check input path
    if 0 == exist('input_folder')
        input_folder = [pwd '/'];
    elseif length(input_folder) < 2
        if input_folder(2) ~= ':'
            input_folder = [pwd '/' input_folder];
        end
    end
    if input_folder(length(input_folder)) ~= '\' && input_folder(length(input_folder)) ~= '/'
        input_folder = [input_folder '/'];
    end

    % check output path
    if 0 == exist('output_folder')
        output_folder = [pwd '/'];
    elseif length(output_folder) < 2 
        if output_folder(2) ~= ':'
            output_folder = [pwd '/' output_folder];  
        end
    end
    if output_folder(length(output_folder)) ~= '\' && output_folder(length(output_folder)) ~= '/'
        output_folder = [output_folder '/'];
    end
    mkdir(output_folder);

end