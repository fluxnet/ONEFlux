function [Cp2, Cp3, s2, s3] = initValues()

    % Assign NaN to Cp2 and Cp3 in one go
    [Cp2, Cp3] = deal(NaN);

    % Initialize s2 as an empty struct
    s2 = struct();

    % Use deal to assign NaN to each field of s2 individually
    [s2.n,   s2.Cp,  s2.Fmax, s2.p, ...
     s2.b0,  s2.b1,  s2.b2,   s2.c2, ...
     s2.cib0, s2.cib1, s2.cic2] = deal(NaN);

    % Copy s2 to s3
    s3 = s2;
end