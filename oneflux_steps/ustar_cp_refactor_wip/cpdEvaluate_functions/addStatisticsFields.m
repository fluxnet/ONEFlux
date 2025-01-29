function xs = addStatisticsFields(xs, t, r, p, T, itStrata)
    xs.mt = mean(t(itStrata));
    xs.ti = t(itStrata(1));
    xs.tf = t(itStrata(end));
    xs.ruStarVsT = r(2, 1);
    xs.puStarVsT = p(2, 1);
    xs.mT = mean(T(itStrata));
    xs.ciT = 0.5 * diff(prctile(T(itStrata), [2.5, 97.5]));
end